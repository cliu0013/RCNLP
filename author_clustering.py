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
import argparse
import Oger
import numpy as np
from sklearn.decomposition import PCA
from core.converters.RCNLPPosConverter import RCNLPPosConverter
from core.tools.RCNLPLogging import RCNLPLogging
from core.nodes.RCNLPWordReservoirNode import RCNLPWordReservoirNode
from core.tools.RCNLPPlotGenerator import RCNLPPlotGenerator
import mdp

#########################################################################
#
# Experience settings
#
#########################################################################

# Exp. info
ex_name = "Author clustering Experience"
ex_instance = "Author clustering, PCA"

# Reservoir Properties
rc_leak_rate = 0.05  # Leak rate
rc_input_scaling = 0.5  # Input scaling
rc_size = 100  # Reservoir size
rc_spectral_radius = 0.9  # Spectral radius
rc_word_sparsity = 0.5

# Data set properties
ds_data_set_size = 40  # Data set size (number of samples)
ds_memory_length = 1200  # How long time to remember the entry
ds_training_length = 30  # Training set length (number of samples)
ds_test_length = ds_data_set_size - ds_training_length
ds_sample_length = 3000  # Length of a sample
ds_slopping_memory = False  # Is the memory slowly fading away?
ds_sparsity = 0  # Number of samples with no switching

####################################################
# Function
####################################################

# Create a reservoir
def create_reservoir(n_symbols, word_sparsity, size, input_scaling, leak_rate, spectral_radius):
    """
    Create a reservoir.
    :param input_dim:
    :param output_dim:
    :param input_scaling:
    :param leak_rate:
    :param t_in:
    :param t_out:
    :return:
    """
    # Create the reservoir
    reservoir = RCNLPWordReservoirNode(input_dim=n_symbols, output_dim=size, input_scaling=input_scaling,
                                       leak_rate=leak_rate, spectral_radius=spectral_radius,
                                       word_sparsity=word_sparsity)

    # Create the flow
    r_flow = mdp.Flow([reservoir], verbose=1)

    return r_flow
# end create_reservoir


# Generate reservoir states
def generate_reservoir_states(the_flow, filename, remove_startup=0):
    # Convert the text to Temporal Vector Representation
    converter = RCNLPPosConverter()
    doc_array = converter(io.open(filename, 'r').read())
    print("Dimensions of the TVR : " + str(doc_array.shape))

    # Display the Temporal Vector Representation
    plot = RCNLPPlotGenerator(title=ex_name, n_plots=1)
    plot.add_sub_plot(title=ex_instance + ", TVR", x_label="Time", y_label="Symbols")
    plot.imshow(np.transpose(doc_array), cmap='Greys')
    logging.save_plot(plot)

    # Generate the reservoir state
    states = the_flow(doc_array)[remove_startup:]
    print("Dimensions of the resulting reservoir states : " + str(states.shape))

    # Display reservoir states
    plot = RCNLPPlotGenerator(title=ex_name, n_plots=1)
    plot.add_sub_plot(title=ex_instance + ", Reservoir states", x_label="Time", y_label="Neurons")
    plot.imshow(np.transpose(states), cmap='Greys')
    logging.save_plot(plot)

    return states
# end generate_reservoir_states


# Generate PCA image
def generate_pca_image(states1, states2, index1, index2):
    n_samples = states1.shape[0] + states2.shape[0]
    n_ratio = 256.0 / n_samples
    image = np.zeros((256, 256, 3))
    for s in states1:
        v1 = s[index1]
        v2 = s[index2]
        image[int((v1+1)*128), int((v2+1)*128), 1] += n_ratio
    # end for
    for s in states2:
        v1 = s[index1]
        v2 = s[index2]
        image[int((v1+1)*128), int((v2+1)*128), 2] += n_ratio
    # end for
    return image
# end generate_pca_image

####################################################
# Main function
####################################################

if __name__ == "__main__":

    # Argument parser
    parser = argparse.ArgumentParser(description="RCNLP - Author clustering with Part-Of-Speech to Echo State Network")

    # Argument
    parser.add_argument("--author1", type=str, help="First author text directory")
    parser.add_argument("--author2", type=str, help="Second author text directory")
    parser.add_argument("--startup", type=int, help="Number of start-up states to remove")
    parser.add_argument("--ncomponents", type=int, help="Number of principal component to analyse")
    parser.add_argument("--nfile", type=int, help="Number of text files to analyze")
    parser.add_argument("--lang", type=str, help="Language (ar, en, es, pt)", default='en')
    args = parser.parse_args()

    # Logging
    logging = RCNLPLogging(exp_name=ex_name, exp_inst=ex_instance,
                           exp_value=RCNLPLogging.generate_experience_name(locals()))
    logging.save_globals()
    logging.save_variables(locals())

    # Create a reservoir
    flow = create_reservoir(14, rc_word_sparsity, rc_size, rc_input_scaling, rc_leak_rate,
                            rc_spectral_radius)

    # Generate states for first author
    state1 = generate_reservoir_states(flow, args.author1, args.startup)

    # Generate states for second author
    state2 = generate_reservoir_states(flow, args.author2, args.startup)

    # Join states
    join_states = np.vstack((state1, state2))
    plot = RCNLPPlotGenerator(title=ex_name, n_plots=1)
    plot.add_sub_plot(title=ex_instance + ", Joined Reservoir states", x_label="Time", y_label="Neurons")
    plot.imshow(np.transpose(join_states), cmap='Greys')
    logging.save_plot(plot)
    print("Dimensions of joined states : " + str(join_states.shape))

    # PCA
    pca = PCA(n_components=args.ncomponents)
    pca.fit(join_states)

    # Generate PCA image
    image = generate_pca_image(pca.transform(state1), pca.transform(state2), 0, 1)
    plot = RCNLPPlotGenerator(title=ex_name, n_plots=1)
    plot.add_sub_plot(title=ex_instance + ", PCA", x_label="Second principal component", y_label="First principal component")
    plot.imshow(image)
    logging.save_plot(plot)

    # Open logging dir
    logging.open_dir()

# end if