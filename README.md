# Laboratorium AI NLP

![Python](https://img.shields.io/badge/Python-3.10.13-blue.svg)
![License](https://img.shields.io/badge/License-MIT-green.svg)
![Poetry](https://img.shields.io/badge/Build-Poetry-blue.svg)

**Laboratorium AI NLP** is a Python package for natural language processing (NLP). It processes text data from JSON files, performs various NLP tasks such as keyword detection, question identification, and word frequency analysis, and saves the results in JSON files. The package uses [spaCy](https://spacy.io/) with the German language model `de_core_news_lg` for high-quality results.

## Table of Contents

- [Laboratorium AI NLP](#laboratorium-ai-nlp)
  - [Table of Contents](#table-of-contents)
  - [Overview](#overview)
    - [Key Features](#key-features)
  - [Installation and Build](#installation-and-build)
  - [Usage](#usage)
    - [CLI Usage with File Descriptors](#cli-usage-with-file-descriptors)
      - [1. Start Module and Load Resources](#1-start-module-and-load-resources)
      - [2. Wait for "ready" Signal](#2-wait-for-ready-signal)
      - [3. Process Files](#3-process-files)
    - [Example Shell Script](#example-shell-script)
  - [License](#license)

## Overview

**Laboratorium AI NLP** provides a simple way to process text data and extract linguistic features. It supports various NLP tasks and enables customization through configuration files. The package leverages spaCy and other NLP libraries to provide accurate and efficient text processing.

### Key Features

- **Text Processing:** Analysis of text data from JSON files.
- **Keyword Detection:** Identification of keywords and negative words in the text.
- **Question Detection:** Identification of open and closed questions in the text.
- **Word Counts and Frequencies:** Counts of unique nouns, verbs, adjectives, and their frequencies based on a word frequency list.
- **Flexible Configuration:** Customization of resources and settings.

## Installation and Build

This package is managed with [Poetry](https://python-poetry.org/). Follow these steps to install and build the package:

1. **Clone Repository:**

   ```bash
   git clone https://github.com/uzl-cosy/cosy-ai-nlp.git
   cd cosy-ai-nlp
   ```

2. **Install Dependencies:**

   ```bash
   poetry install
   ```

3. **Activate Virtual Environment:**

   ```bash
   poetry shell
   ```

4. **Build Package:**

   ```bash
   poetry build
   ```

   This command creates the distributable files in the `dist/` directory.

## Usage

The package runs as a persistent module through the command line interface (CLI). It enables processing of JSON files containing text data and outputs the analysis to JSON files using file descriptors. Communication occurs through a pipe, where the module sends "ready" once the resources are loaded and ready for processing.

### CLI Usage with File Descriptors

#### 1. Start Module and Load Resources

Start the NLP module via CLI. The module loads the resources (NLP model, word frequency list, question words) and signals through the file descriptor when it's ready.

```bash
python -m laboratorium_ai_nlp -f <FD>
```

**Parameters:**

- `-f, --fd`: File descriptor for pipe communication.

**Example:**

```bash
python -m laboratorium_ai_nlp -f 3
```

#### 2. Wait for "ready" Signal

After starting the module, it loads the necessary resources. Once loaded, the module sends a "ready" signal through the specified file descriptor.

#### 3. Process Files

Pass the input file paths and output file path through the pipe. The module processes the files and sends a "done" signal once processing is complete.

**Input Files:**

- **Input JSON File:** Contains the text data to be processed. It should have either a `"Text"` key (string) or a `"Sentences"` key (list of strings), or both.
- **Keyword List JSON File:** Contains `"Keywords"` and `"Negative Words"` lists for keyword detection.

**Example:**

```bash
echo "path/to/input_text.json,path/to/keyword_list.json,path/to/output_analysis.json" >&3
```

**Description:**

- The `echo` command sends input and output file paths through file descriptor `3`.
- The module receives the paths, processes the text data, and saves the analysis result in the output JSON file.
- Upon completion, the module sends a "done" signal through the file descriptor.

**Complete Flow:**

1. **Start the NLP Module:**

   ```bash
   python -m laboratorium_ai_nlp -f 3
   ```

2. **Send File Paths for Processing:**

   ```bash
   echo "path/to/input_text.json,path/to/keyword_list.json,path/to/output_analysis.json" >&3
   ```

3. **Wait for "done" Signal:**

   After sending the file paths, wait for the module to process the files. It will send a "done" signal when processing is complete.

4. **Repeat Step 2 for Additional Files:**

   You can process additional files by repeating the file path input:

   ```bash
   echo "path/to/another_input_text.json,path/to/keyword_list.json,path/to/another_output_analysis.json" >&3
   ```

### Example Shell Script

Here's an example of using the NLP package in a shell script:

```bash
#!/bin/bash

# Open a file descriptor (e.g., 3) for pipe communication

exec 3<>/dev/null

# Start the NLP module in background and connect the file descriptor

python -m laboratorium_ai_nlp -f 3 &

# Store NLP module's PID for later termination

NLP_PID=$!

# Wait for "ready" signal

read -u 3 signal
if [ "$signal" = "ready" ]; then
echo "Model is ready for processing."

      # Send input and output paths
      echo "path/to/input_text.json,path/to/keyword_list.json,path/to/output_analysis.json" >&3

      # Wait for "done" signal
      read -u 3 signal_done
      if [ "$signal_done" = "done" ]; then
            echo "Processing complete."
      fi

      # Additional processing can be added here
      echo "path/to/another_input_text.json,path/to/keyword_list.json,path/to/another_output_analysis.json" >&3

      # Wait for "done" signal again
      read -u 3 signal_done
      if [ "$signal_done" = "done" ]; then
            echo "Additional processing complete."
      fi

fi

# Close the file descriptor

exec 3>&-
```

## License

This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for details.
