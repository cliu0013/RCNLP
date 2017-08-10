#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# File : core.classifiers.RCNLPTextClassifier.py
# Description : Echo State Network for text classification.
# Auteur : Nils Schaetti <nils.schaetti@unine.ch>
# Date : 01.02.2017 17:59:05
# Lieu : Nyon, Suisse
#
# This file is part of the Reservoir Computing NLP Project.
# The Reservoir Computing Memory Project is a set of free software:
# you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# Foobar is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
# You should have received a copy of the GNU General Public License
# along with Foobar.  If not, see <http://www.gnu.org/licenses/>.
#

import io
import os
import argparse
import numpy as np
from core.converters.OneHotConverter import OneHotConverter
from core.classifiers.EchoWordClassifier import EchoWordClassifier
import logging
from core.embeddings.Word2Vec import Word2Vec
from sklearn.manifold import TSNE
import pylab as plt
import math
from scipy.spatial.distance import euclidean

#########################################################################
# Experience settings
#########################################################################

# Exp. info
ex_name = "Authorship Attribution"
ex_instance = "Two Authors One-hot representations"

# Reservoir Properties
rc_leak_rate = 0.5  # Leak rate
rc_input_scaling = 1.0  # Input scaling
rc_size = 2000  # Reservoir size
rc_spectral_radius = 0.99  # Spectral radius
rc_w_sparsity = 0.1
rc_input_sparsity = 0.005

####################################################
# Functions
####################################################


def get_similar_documents(document_index, document_embeddings):
    similarities = list()
    for n in range(document_embeddings.shape[1]):
        if n != document_index:
            distance = euclidean(document_embeddings[:, document_index], document_embeddings[:, n])
            similarities.append((n, distance))
        # end if
    # end for

    # Sort
    similarities.sort(key=lambda tup: tup[1])

    return similarities
# end get_similar_documents

####################################################
# Main function
####################################################

if __name__ == "__main__":

    # Argument parser
    parser = argparse.ArgumentParser(
        description="RCNLP - Compare the Echo Text Classifier to other models with two authors")

    # Argument
    parser.add_argument("--dataset", type=str, help="Dataset's directory")
    parser.add_argument("--n-authors", type=int, help="Number of authors", default=10)
    parser.add_argument("--n-documents", type=int, help="Number of documents per authors", default=10)
    parser.add_argument("--lang", type=str, help="Language (en_core_web_md, ar, en, es, pt)", default='en_core_web_md')
    parser.add_argument("--verbose", action='store_true', help="Verbose mode", default=False)
    parser.add_argument("--debug", action='store_true', help="Debug mode", default=False)
    parser.add_argument("--voc-size", type=int, help="Vocabulary size", default=5000, required=True)
    parser.add_argument("--log-level", type=int, help="Log level", default=20)
    parser.add_argument("--sparse", action='store_true', help="Sparse matrix?", default=False)
    parser.add_argument("--fig-size", type=float, help="Figure size (pixels)", default=1024.0)
    args = parser.parse_args()

    # Init logging
    logging.basicConfig(level=args.log_level)
    logger = logging.getLogger(name="RCNLP")

    # Word2Vec
    word2vec = Word2Vec(dim=args.voc_size, mapper='one-hot')

    # Choose a text to symbol converter
    converter = OneHotConverter(lang=args.lang, voc_size=args.voc_size, word2vec=word2vec)

    # Total number of docs
    n_total_docs = args.n_authors * args.n_documents

    # Create Echo Word Classifier
    classifier = EchoWordClassifier(classes=range(n_total_docs), size=rc_size, input_scaling=rc_input_scaling,
                                    leak_rate=rc_leak_rate,
                                    input_sparsity=rc_input_sparsity, converter=converter,
                                    spectral_radius=rc_spectral_radius, w_sparsity=rc_w_sparsity,
                                    use_sparse_matrix=args.sparse)

    # Add examples
    document_index = 0
    for author_id in np.arange(1, args.n_authors+1):
        author_path = os.path.join(args.dataset, "total", author_id)
        for file_index in range(args.n_documents):
            file_path = os.path.join(author_path, str(file_index) + ".txt")
            logger.info(u"Adding document {} as {}".format(file_path, document_index))
            classifier.train(io.open(file_path, 'r').read(), document_index)
            document_index += 1
        # end for
    # end for

    # Finalize model training
    classifier.finalize(verbose=args.verbose)

    # Get documents embeddings
    document_embeddings = classifier.get_embeddings()
    logger.info(u"Document embeddings shape : {}".format(document_embeddings.shape))

    # Display similar doc for the first document of each author
    for document_index in np.arange(0, n_total_docs, args.n_authors):
        logger.info(u"Documents similar to {} : {}".format(document_index,
                                                           get_similar_documents(document_index, document_embeddings)))
    # end for

    # Reduce with t-SNE
    model = TSNE(n_components=2, random_state=0)
    reduced_matrix = model.fit_transform(document_embeddings.T)

    # Word embedding matrix's size
    logger.info(u"Reduced matrix's size : {}".format(reduced_matrix.shape))

    # Show t-SNE
    plt.figure(figsize=(args.fig_size*0.003, args.fig_size*0.003), dpi=300)
    max_x = np.amax(reduced_matrix, axis=0)[0]
    max_y = np.amax(reduced_matrix, axis=0)[1]
    min_x = np.amin(reduced_matrix, axis=0)[0]
    min_y = np.amin(reduced_matrix, axis=0)[1]
    plt.xlim((min_x * 1.2, max_x * 1.2))
    plt.ylim((min_y * 1.2, max_y * 1.2))
    for document_index in range(n_total_docs):
        author_index = int(float(document_index) / float(args.n_authors))
        plt.scatter(reduced_matrix[document_index, 0], reduced_matrix[document_index, 1], 0.5)
        plt.text(reduced_matrix[document_index, 0], reduced_matrix[document_index, 1], str(author_index), fontsize=2.5)
    # end for

# end if