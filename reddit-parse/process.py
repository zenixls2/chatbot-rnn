from __future__ import print_function
import os, json, re, sys, argparse

OUTPUT_FILE = 'output.txt'
REPORT_FILE = 'RC_report.txt'

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--input_file', type=str, default='reddit_data',
            help='data file containing json reddit data')
    parser.add_argument('--logdir', type=str, default='standard',
            help='directory to save the output report')
    parser.add_argument('--config_file', type=str,
            default='parser_config_standard.json',
            help='json parameters for parsing')
    parser.add_argument('--comment_cache_size', type=int, default=500000,
            help='max number of comments to cache in memory before flushing')
    parser.add_argument('--output_file_size', type=int, default=2e8,
            help='max number of comments to cache in memory before flushing')
    parser.add_argument('--print_every', type=int, default=1000,
            help='print an update to the screen at this frequency')
    args = parser.parse_args()
    parse_main(args)

class RedditComment(object):
    def __init__(self, obj):
        self.body = obj['body']
        self.score = obj['score']
        self.author = obj['author']
        # parent_id in raw data come with tc1_dxvg23 like pattern.
        # The tc1_ part is not needed here
        self.parent_id = obj['parent_id'].split('_')[1]
        self.timestamp = obj['created_utc']
        # subcomment for a comment, use timestamp for defining layers
        self.child_id = []

def raw_data_generator(path):
    with open(path, 'rb') as f:
        for line in f:
            yield line

space = re.compile('[ \t\n]+')
carets = re.compile('\^')
blackslash = re.compile('\\\\')
less_than = re.compile('&lt;')
greater_than = re.compile('&gt;')
logic_and = re.compile('&amp;')

def post_qualifies(obj, rblacklist, rwhitelist, sblacklist):
    body = obj['body'].encode('ascii', 'ignore').strip()
    post_length = len(body)
    if post_length < 4 or post_length > 200:
        return False
    subreddit = obj['subreddit']
    if len(rwhitelist) > 0 and subreddit not in rwhitelist:
        return False
    if len(rblacklist) > 0 and subreddit in rwhitelist:
        return False
    if sblacklist:
        if sblacklist.match(body):
            return False
    body = logic_and.sub('&',
        greater_than.sub('>',
        less_than.sub('<',
        blackslash.sub('',
        carets.sub('',
        space.sub(' ', body))))))
    post_length = len(body)
    if post_length < 4 or post_length > 200:
        return False
    obj['body'] = body
    return True

def process_comment_cache(comment_dict, print_every):
    i = 0
    for id, comment in comment_dict.iteritems():
        if i % print_every == 0:
            print("\r"+str(i)+'comments processed', end='')
        if comment.parent_id is None:
            continue
        parent = comment_dict.get(comment.parent_id, None)
        if parent is None or comment.parent_id == id:
            comment.parent_id = None
            continue
        else:
            parent.child_id.append((id, comment.timestamp))
        i += 1


def old_process_comment_cache(comment_dict, print_every):
    i = 0
    for id, comment in comment_dict.iteritems():
        if i % print_every == 0:
            print("\r"+str(i)+'comments processed', end='')
        if comment.parent_id is None:
            continue
        parent = comment_dict.get(comment.parent_id, None)
        if parent is None:
            comment.parent_id = None
            continue
        if parent.child_id is None:
            parent.child_id = id
        else:
            parent_previous_child = comment_dict[parent.child_id]
            grandparent = comment_dict.get(parent.parent_id, None)
            if grandparent and (comment.author == grandparent.author or
                parent_previous_child.author != grandparent.author and
                comment.score > parent_previous_child.score):
                parent.child_id = id
        i += 1

def write_comment_cache(comment_dict, output_file, print_every):
    i = 0
    for k, v in comment_dict.iteritems():
        if v.parent_id is None and len(v.child_id) > 0:
            children = sorted(v.child_id, key=lambda x: -x[1])
            output_string = '> ' + v.body + '\n'
            for child in children:
                output_string += '> ' + comment_dict.get(child[0]).body + '\n'
            output_file.write(output_string + '\n')
            i += len(v.child_id)
    print("\r"+str(i)+'comments written.', end='')



def old_write_comment_cache(comment_dict, output_file, print_every):
    i = 0
    for k, v in comment_dict.iteritems():
        if v.parent_id is None and v.child_id is not None:
            comment = v
            depth = 0
            output_string = ""
            while comment is not None:
                depth += 1
                output_string += '> ' + comment.body + '\n'
                comment = comment_dict.get(comment.child_id, None)
                if not comment and depth > 3:
                    output_file.write(output_string + '\n')
                    i += depth
    print i, 'comments Written'
    sys.stdout.flush()

def write_report(report_file_path, subreddit_dict):
    subreddit_list = sorted(subreddit_dict.items(), key=lambda x: -x[1])
    with open(report_file_path, "wb") as f:
        for item in subreddit_list:
            f.write("{}: {}\n".format(*item))

def parse_main(c):
    with open(c.config_file, 'rb') as f:
        config = json.load(f)
    subreddit_blacklist = set(config['subreddit_blacklist'])
    subreddit_whitelist = set(config['subreddit_whitelist'])
    substring_blacklist = config['substring_blacklist']
    substring_blacklist_regex = re.compile('|'.join(
        map(
            lambda x: re.escape(x),
            substring_blacklist
        )
    ))

    if not os.path.exists(c.logdir):
        os.mkdir(c.logdir)
    subreddit_dict = {}
    comment_dict = {}
    cache_count = 0
    raw_data = open(c.input_file, 'rb')
    outputfile = open(os.path.join(c.logdir, OUTPUT_FILE), 'wb')
    i = 0
    for line in raw_data:
        # for multiple line json
        text = ''
        comment = {}
        if len(line) > 1:
            if line[-1] == '}' or line[-2] == '}':
                text += line
                comment = json.loads(line)
            else:
                text += line
                continue
        else:
            continue
        if post_qualifies(comment, subreddit_blacklist, subreddit_whitelist,
                substring_blacklist_regex):
            sub = comment['subreddit']
            subreddit_dict[sub] = subreddit_dict.get(sub, 0) + 1
            comment_dict[comment['id']] = RedditComment(comment)
            cache_count += 1
            if cache_count % c.print_every == 0:
                print("\r"+str(cache_count)+'comments Cached', end='')
            if cache_count > c.comment_cache_size:
                process_comment_cache(comment_dict, c.print_every)
                write_comment_cache(comment_dict, outputfile, c.print_every)
                write_report(os.path.join(c.logdir, REPORT_FILE), subreddit_dict)
                comment_dict = {}
                cache_count = 0
        i += 1
    print "\nRead all", i, "lines."
    process_comment_cache(comment_dict, c.print_every)
    write_comment_cache(comment_dict, outputfile, c.print_every)
    write_report(os.path.join(c.logdir, REPORT_FILE), subreddit_dict)
    raw_data.close()

if __name__ == '__main__':
    main()
