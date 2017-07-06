# chatbot-rnn
A toy chatbot powered by deep learning and trained on data from Reddit.

Here is a sample chat transcript (not cherry-picked). Lines that start with ">" are me; the lines without ">" are the chatbot's responses.

```
$ python chatbot.py
Creating model...
Restoring weights...

> Hi, how are you?
 It's all good, I'm going to bed now but I'll see if I can get home tomorrow. I'll get back to you.
> Don't go to bed just yet
 That's great, what do you think of me?
> I think you're a pretty interesting conversationalist
 Thank you, I appreciate it.
> No problem. What do you think of me?
 Well, you know, that's fine. I don't think I could get behind any of them.
> I see. Is anyone asking you to get behind them?  
 Of course not. I don't want to make myself look bad.
> Yeah, I understand. So what's new?
 Anything that isn't childish and ignorant of yourself.
> Do you think I'm childish and ignorant?
 Yes. Yes you are.
> Why would you say that?
 I don't think you know what you are talking about.
> But we've only just started talking!
 Yeah.. I guess I shouldn't have gotten over it...
> It's all right.
 That's not what I meant.
 ```

## Get Started

- Clone this project to your computer.

- **Install [Tensorflow](http://www.tensorflow.org/)**. To run a pretrained model, the CPU-only installation should suffice. If you want to train your own models, you'll need the GPU installation of Tensorflow (and a powerful CUDA-compatible GPU).

### Run my pre-trained model

- **Download [my pre-trained model](https://mega.nz/#!KI5z3JQA!WITf7HC8ISAh7tTMVdGH0fncsQHCm0s-NafuHHhVX18)** (51 MB). The bzip2 file extracts into a folder named "reddit". Place that folder into the "models" directory of this project. Notice this data is not fully trained, and might not perform as well as the example shown in this README.

- **Run the chatbot**. Open a terminal session and run `python chatbot.py`. Warning: this pre-trained model was trained on a diverse set of frequently off-color Reddit comments. It can (and eventually will) say things that are offensive, disturbing, bizarre or sexually explicit. It may insult minorities, it may call you names, it may accuse you of being a pedophile, it may try to seduce you. Please don't use the chatbot if these possibilities would distress you!

Try playing around with the arguments to `chatbot.py` to obtain better samples:

- **beam_width**: By default, `chatbot.py` will use beam search with a beam width of 2 to sample responses. Set this higher for more careful, more conservative (and slower) responses, or set it to 1 to disable beam search.

- **temperature**: At each step, the model ascribes a certain probability to each character. Temperature can adjust the probability distribution. 1.0 is neutral (and the default), lower values increase high probability values and decrease lower probability values to make the choices more conservative, and higher values will do the reverse. Values outside of the range of 0.5-1.5 are unlikely to give coherent results.

- **relevance**: Two models are run in parallel: the primary model and the mask model. The mask model is scaled by the relevance value, and then the probabilities of the primary model are combined according to equation 9 in [Li, Jiwei, et al. "A diversity-promoting objective function for neural conversation models." arXiv preprint arXiv:1510.03055 (2015)](https://arxiv.org/abs/1510.03055). The state of the mask model is reset upon each newline character. The net effect is that the model is encouraged to choose a line of dialogue that is most relevant to the prior line of dialogue, even if a more generic response (e.g. "I don't know anything about that") may be more absolutely probable. Higher relevance values put more pressure on the model to produce relevant responses, at the cost of the coherence of the responses. Going much above 0.4 compromises the quality of the responses. Setting it to a negative value disables relevance, and this is the default, because I'm not confident that it qualitatively improves the outputs and it halves the speed of sampling.

These values can also be manipulated during a chat, and the model state can be reset, without restarting the chatbot:

```
$ python chatbot.py
Creating model...
Restoring weights...

> --temperature 1.3
[Temperature set to 1.3]

> --relevance 0.3
[Relevance set to 0.3]

> --relevance -1
[Relevance disabled]

> --beam_width 5
[Beam width set to 5]

> --reset
[Model state reset]
```

### Get training data

If you'd like to train your own model, you'll need training data. There are a few options here.

- **Provide your own training data.** Training data should be one or more newline-delimited text files. Each line of dialogue should begin with "> " and end with a newline. You'll need a lot of it. Several megabytes of uncompressed text is probably the minimum, and even that may not suffice if you want to train a large model. Text can be provided as raw .txt files or as bzip2-compressed (.bz2) files.

- **Simulate the United States Supreme Court.** I've included a corpus of United States Supreme Court oral argument transcripts (2.7 MB compressed) in the project under the `data/scotus` directory.

- **Use Reddit data.** This is what the pre-trained model was trained on:

  The trained data is based on Reddit comment data provided from [here](http://files.pushshift.io/reddit/comments/RC_2017-05.bz2)(~7 GB compressed). You could find data from other months or in any other format from this [file sharing site](http://files.pushshift.io/reddit/). Extract the individual bzip2 (.bz2) files contained in these archives.

  Once you have your raw reddit data, place it in the `reddit-parse/reddit_data` subdirectory and use the `preprocess.py` script included in the project file to convert them into text files of appropriately formatted conversations. After preprocess is done, compress the `output.txt` using bzip2 tool and put it in data/redddit folder. This script chooses qualifying comments (must be under 200 characters, can't contain certain substrings such as 'http://', can't have been posted on certain subreddits) and assembles them into conversations of at least four lines. Coming up with good rules to curate conversations from raw reddit data is more art than science. I encourage you to play around with the parameters in the included `parser_config_standard.json` file, or to mess around with the parsing script itself, to come up with an interesting data set.

  Please be aware that there is a *lot* of Reddit data included in the folder. It is very easy to run out of memory or hard drive space. The original result provided by the author use a 160GB version and is quite easily to exhaust all of your memory.

Once you have training data in hand (and located in a subdirectory of the `data` directory):

### Train your own model

- **Train.** Use `train.py` to train the model. The default hyperparameters (four layers of 1500 GRUs per layer) are the best that I've found, and are what I used to train the pre-trained model for about 37 days. These hyperparameters will just about fill the memory of a Titan X GPU, so if you have a smaller GPU, you will need to adjust them accordingly -- most straightforwardly, by reducing the batch size.

  Training can be interrupted with crtl-c at any time, and will immediately save the model when interrupted. Training can be resumed on a saved model and will automatically carry on from where it was interrupted.

  ![Alt text](/img/chatbot-training.png?raw=true)

## Thanks

Thanks to Andrej Karpathy for his excellent [char-rnn](https://github.com/karpathy/char-rnn) repo, and to Sherjil Ozair for his [tensorflow port](https://github.com/sherjilozair/char-rnn-tensorflow) of char-rnn, which this repo is based on.
