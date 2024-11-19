import argparse
import json
import os
import pandas as pd
import re
import spacy
import string
import sys


from collections import Counter
from importlib.resources import files
from fuzzywuzzy import fuzz
from nltk.tokenize import sent_tokenize

# Global file descriptor variable, defaulting to None
FD = None


def send_pipe_message(message):
    global FD
    if FD is not None:
        os.write(FD, message.encode("utf-8") + b"\n")


def load_resources():
    # Load the Spacy model
    model = spacy.load("de_core_news_lg")

    # Load word frequency list
    word_frequency_list = pd.read_csv(
        files("laboratorium_ai_nlp.data").joinpath("word_frequency_list_COSY.csv"),
        sep="\t",
        converters={"strings": str},
        keep_default_na=False,
    )

    # Initialize list of german question words
    question_words = [
        "wo",
        "wohin",
        "woher",
        "woran",
        "worin",
        "worauf",
        "worunter",
        "wovor",
        "wohinter",
        "woneben",
        "wofür",
        "wozu",
        "womit",
        "wodurch",
        "worum",
        "worüber",
        "wobei",
        "wovon",
        "woraus",
        "wer",
        "welche",
        "welcher",
        "wem",
        "wen",
        "welches",
        "welchen",
        "welchem",
        "weshalb",
        "wessen",
        "weswegen",
        "wie",
        "wieweit",
        "wieso",
        "was",
        "wann",
        "warum",
    ]

    return model, word_frequency_list, question_words


def count_words_unique(text, nlp_model):
    """
    This function counts unique nouns, verbs and adjectives in a text using an NLP model.

    :param text: string
    :param nlp_model: string
    :return n_word_counts: counter
    :return v_word_counts: counter
    :return a_word_counts: counter
    """

    doc = nlp_model(text)

    # Initialize counters
    n_word_counts = Counter()
    v_word_counts = Counter()
    a_word_counts = Counter()

    # Iterate through tokens in doc
    for token in doc:
        # Check if the token is a noun and not a stop word
        if token.pos_ == "NOUN" or token.pos_ == "PROPN":
            n_word_counts[token.text] += 1  # Increment the count of the noun counter

        if token.pos_ == "VERB":
            v_word_counts[
                token.text.lower()
            ] += 1  # Increment the count of the verb counter

        if token.pos_ == "ADJ":
            a_word_counts[
                token.text.lower()
            ] += 1  # Increment the count of the adjective counter

    return n_word_counts, v_word_counts, a_word_counts


def detect_questions(in_text, w_words):
    """
    This function checks whether a sentence in in_text is a question or not. Therefore, the transcript in in_text is
    divided into sentences using punctuations and it is specifically checked whether a sentence ends with a question
    mark or not.
    In cases a question mark is present at the end of the sentence, it is further checked if it is a open or closed
    question by looking for specific question words (e. g. wie, was, warum), because these words indicate an open
    question.
    List with the values 0, 1, 2, whose length corresponds to the number of sentences in in_text.
             With 0 indicating a sentence is not a question, 1 indicating an open question and 2 indicating a closed question.


    :param in_text: String
    :param w_words: List of question words
    :return question list:

    """
    question_list = []
    sentences = re.findall(
        r"[^.!?]+[.!?]", in_text
    )  # Split in_text into a list sentences

    for in_sentence in sentences:
        if in_sentence.strip().endswith("?"):
            for s in in_sentence.strip().split(" "):
                contains_word = any(word in s.lower() for word in w_words)

                if contains_word:
                    question_list.append(1)  # Open Question
                    break
                else:
                    question_list.append(2)  # Closed Questions
                    break
        else:
            question_list.append(0)  # No Question
    return question_list


def find_keyword_position(doc, kwords, nwords):
    """
    :param doc:
    :param kwords:
    :param nwords:
    :return word_pos_vector:
    """

    word_pos_vector = [0] * len(doc)  # Initialize a binary vector with zeros

    for idx, token in enumerate(doc):
        token_lemma = token.lemma_

        best_match = None
        best_match_position = -1
        for keyword in kwords:
            similarity = fuzz.ratio(token_lemma.lower(), keyword.lower())

            threshold = 80
            if similarity > threshold and (
                best_match is None or similarity > best_match
            ):
                best_match = similarity
                best_match_position = idx

            if best_match_position > -1:
                word_pos_vector[best_match_position] = 1

        best_match = None
        best_match_position = -1
        for keyword in nwords:
            similarity = fuzz.ratio(token_lemma.lower(), keyword.lower())

            threshold = 80
            if similarity > threshold and (
                best_match is None or similarity > best_match
            ):
                best_match = similarity
                best_match_position = idx

            if best_match_position > -1:
                word_pos_vector[best_match_position] = -1

    return word_pos_vector


def get_word_frequencies(words_counts_counter, n_f_list):
    """
    This function calculates the word frequencies.

    :param noun_counts_counter:
    :param n_f_list:
    :return word_frequencies: dict
    """

    word_frequencies = {}
    for counter_item in enumerate(words_counts_counter.items()):
        counter_item_info = counter_item[1]
        counter_word = counter_item_info[0]
        word_idx = n_f_list["Word"].isin([counter_word])

        try:
            word_frequency = n_f_list[word_idx]["Frequency"].values[0]
            word_frequency = word_frequency.item()

        except:
            word_frequency = 0

        tmp_dict = {counter_word: word_frequency}
        word_frequencies = {**word_frequencies, **tmp_dict}

    return word_frequencies


def process_json(
    nlp_model, wf_list, w_word_list, inp_path_json, inp_word_list, out_path_json
):
    """
    This function

    :param nlp_model: NLP Model
    :param wf_list: List
    :param w_word_list: List
    :param inp_path_json: String
    :param inp_word_list: String
    :param out_path_json: String
    """

    with open(inp_word_list) as f:
        keyword_list = json.load(f)

    with open(inp_path_json, "r") as f:
        data = json.load(f)

    if "Sentences" not in data.keys() and "Text" not in data.keys():
        sys.stdout.write("Sentences and Text Key not found. Processing aborted!")
        send_pipe_message("done")
    else:
        if "Text" in data.keys() and "Sentences" not in data.keys():
            text = data["Text"]
            sentences = sent_tokenize(data["Text"], language="german")
            sys.stdout.write("Sentences have to be detected.")
        elif "Text" in data.keys() and "Sentences" in data.keys():
            text = data["Text"]
            sentences = data["Sentences"]
        else:
            sentences = data["Sentences"]
            text = " ".join(sentences)

        kwords = keyword_list["Keywords"]
        kwords = [nlp_model(kword)[0].lemma_ for kword in kwords]

        nwords = keyword_list["Negative Words"]
        nwords = [nlp_model(nword)[0].lemma_ for nword in nwords]

        position_vectors = []
        for sentence in sentences:
            sentence = sentence.translate(str.maketrans("", "", string.punctuation))
            sentence = nlp_model(sentence)
            position_vector = find_keyword_position(sentence, kwords, nwords)
            position_vectors.append(position_vector)

        q_list = detect_questions(text, w_word_list)

        # Initialize word counters
        word_counts_nouns, word_counts_verbs, word_counts_adj = count_words_unique(
            text, nlp_model
        )

        # Convert Counter to Dict
        word_counts_nouns = dict(word_counts_nouns)
        word_counts_verbs = dict(word_counts_verbs)
        word_counts_adj = dict(word_counts_adj)

        # Get word frequencies
        noun_frequency_list = get_word_frequencies(word_counts_nouns, wf_list)
        verbs_frequency_list = get_word_frequencies(word_counts_verbs, wf_list)
        adj_frequency_list = get_word_frequencies(word_counts_adj, wf_list)

        out_dict = {
            "Keyword Position List": position_vectors,
            "Question List": q_list,
            "Noun Counts": word_counts_nouns,
            "Verb Counts": word_counts_verbs,
            "ADJ Counts": word_counts_adj,
            "Noun Frequncies": noun_frequency_list,
            "Verb Frequencies": verbs_frequency_list,
            "Adj Frequencies": adj_frequency_list,
        }

        with open(out_path_json, "w") as f:
            json.dump(out_dict, f, ensure_ascii=False)

        send_pipe_message("done")


def read_io_paths():
    return sys.stdin.readline().strip().split(",")


def main():
    parser = argparse.ArgumentParser(description="Process audio files with Whisper.")
    parser.add_argument(
        "-f", "--fd", type=int, help="Optional file descriptor for pipe communication"
    )
    args = parser.parse_args()

    if args.fd:
        global FD
        FD = args.fd  # Set the global file descriptor only if provided

    nlp_keyword_model, w_frequency_list, question_word_list = load_resources()
    send_pipe_message("ready")

    while True:
        # Read input and output file paths from stdin
        input_path_json, input_path_keyword_list, output_path_json = read_io_paths()
        process_json(
            nlp_keyword_model,
            w_frequency_list,
            question_word_list,
            input_path_json,
            input_path_keyword_list,
            output_path_json,
        )


if __name__ == "__main__":
    main()
