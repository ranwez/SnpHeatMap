"""!
@file main.py
@brief
Create a number of chart related to snp (simple nucleotide polymorphism) analysis

@subsection How to use this file
Python3 [Column that contain gene's names] [Column tha contain the number of snp] [path to a folder
that contain your files] [options]

See string returned by @ref main.help_usage() for information

@subsection chart Charts
    - Quantitative bar chart (-q) : Show the number of gene (y) per number of snp (x)
    - Cumulative bar chart (-c): Show the number of gene (y) that have at least n snp (x)
    - Monoheatmap (-u): Cumulative bar chart but it's a heatmap
    - global heatmap (-g): concatenation of all Monoheatmap

@subsection format Formats
    - as tsv (-t)
    - as png (-k)
    - as svg (-b)
    - as a pop-up (-d)


@section authors Author(s)
  - Created by Marchal Florent on 06/05/2024.
This module has been made in 2024 during an internship at the UMR Agap, GE2pop (France, Montpellier)

@section libs Librairies/Modules
  - os
  - json
  - matplotlib.pyplot
  - sys
  - getopt

"""
# Native libraries
import os
import json
import getopt

try:
    import matplotlib.pyplot as plt
    from PIL import Image

except ModuleNotFoundError as E:
    print(f"Module not found : {E}\n"
          f"Open a terminal and try : "
          f"\n\tpip install matplotlib"
          f"\n\nIf pip is not found, you can install it using : "
          f"\nOn linux or MacOs: "
          f"\n\tpython -m ensurepip --upgrade"
          f"\nOn Windows : "
          f"\n\tpy -m ensurepip --upgrade"
          )
    exit(6)

__author__ = "Marchal Florent"
__credits__ = ["Florent Marchal", "Vetea Jacot", "Concetta Burgarella", "Vincent Ranwez", "Nathalie Chantret"]


# List of arguments used to start this program with Their shorten name, (default value and type)
__getopts__ = {
    # long name:                (shorten_name, (default_value, type))
    #                                           None = (None, str)

    # Arguments:
    "name_column=":             ("n:", None),
    "snp_column=":              ("s:", None),
    "path=":                    ("p:", ("data", str)),

    # Parameters :
    "help": ("h", None),
    "file_separator=":          ("f:", ("\t", str)),
    "output_path=":             ("o:", ("output/", str)),
    "job_name=":                ("j:", ("Unnamed", str)),
    "max_length=":              ("m:", (20, int)),

    # long name:                (shorten_name, (inactive value, active value))
    #                                           None = (True, False)
    "output_warning":           ("w", (True, False)),
    "sort_by_name":             ("r", (True, False)),
    "simplified":               ("i", None),
    "global_heatmap":           ("g", None),
    "quantitative_barchart":    ("q", None),
    "cumulative_barchart":      ("c", None),
    "cumulative_heatmap":       ("u", None),
    "tsv":                      ("t", None),
    "png":                      ("k", None),
    "show":                     ("d", None),
    "svg":                      ("v", None),
    "show_values=":             ("e:", (None, int))
}


def help_usage():
    return ("python3 main.py [Gene name Column] [Snp column] [Path to your files] [Options]"
            f"\nOptions are : "
            f"\n{'\t'.join([      f'{short_key} / {key}, ' if short_key[-1] != ":" 
                            else f'{short_key[:-1]} / {key}, ' for key, (short_key, _) in __getopts__.items()
                            ]
                           )}"
            f"\nSee README.md for more details")


def parse_line(legend: list[str], line: str, separator: str = "\t") -> dict[str, str]:
    """! @brief Turn a line form a flat File with its legend and turn it into a dictionary.
    @param legend : Names all the line's columns. Example: ["A", "B", "C"]
    @param line : Contains all the line's values. Example: "1|2|3|", "1|2|3" ...
    @param separator : The symbol that splits the line's values. Example: "|", "\n", "\t" ...
    @return A dictionary composed of legend's values and line's values.
        Example:  @code {"A": "1", "B": "2", "C": "3"}  @endcode (using previous examples)

    @note The returned dict always contain the same umber of object than legend.
        - If legend > line : part of the legend's values will point to an empty string
        - If legend < line : part of the line will be ignored
    """

    parsed_line = {}
    split_line = line.split(separator)  # Split the line in "columns"

    # Fill parsed_line
    for i, column_name in enumerate(legend):
        cell_value = split_line[i] if i < len(split_line) else ""
        parsed_line[column_name] = cell_value
        i += 1

    return parsed_line


def extract_data_from_table(path: str, key: str, value: str, separator: str = "\t",
                            legend: list = None, filter_: callable = None) -> dict[str, any]:
    """!
    @brief Read a table contained inside a flatFile (e.g. tsv, csv, ...)

    @warning If the column @p key contains the same value multiple times, only the last one is kept.

    @param path : Path to a flatFile.
    @param key : A column name that can be found in the legend. This will be used as a key in the returned dict.
            Example: "Column3"
    @param value : A column name that can be found in the legend. This will be used as a value in the returned dict
            WHEN @p filter returns None or True. Example: "Column2"
    @param separator : The symbol that splits line's values. Example: "|", "\n", "\t" ...
    @param legend : If None: The first non-empty line in the file split using @p separator. Else: A list of column
            names. Example: [Column1, Column2, Column3]
    @param filter_ : A function that accepts 3 arguments: @p key, @p value, and the parsed line (dict). It
            selects/generates the value present next to each key.
                - If it returns True or None: value in the column @p value.
                - If it returns False: this line is ignored.
                - Else: The returned value is used (instead of the content of the column @p value).
    @note filter_ is called one time per line.
    @return A dictionary: {values in the column @p key (values that do not pass @p filter_ are ignored): values in the column @p value OR value returned by @p filter_}
    """
    # Open file
    flux = open(path, "r", encoding="UTF-8")
    data = {}

    # Researched keys and values should be contained inside the legend.
    if legend is not None and (key not in legend or value not in legend):
        raise ValueError(f"Both key ('{key}') and value {value} should be contained inside legend : {legend}")

    # Fill data
    for line in flux:
        # Special cases : empty line | empty file
        if line == "\n" or line == "":
            continue

        # Special cases : Unknown legend
        if legend is None:
            legend = line.split(separator)

            # Researched keys and values should be contained inside the legend.
            if key not in legend or value not in legend:
                raise ValueError(f"Both key ('{key}') and value('{value}') should be contained inside the legend : {legend}")

            if legend[-1][-1] == "\n":
                legend[-1] = legend[-1][:-1]
            continue

        # Parse the line
        parsed_line = parse_line(legend, line, separator)

        # Apply the filter_
        func_result = filter_(key, value, parsed_line) if filter_ else None
        if func_result is False:
            continue

        if func_result is None or func_result is True:
            # Save  parsed_line[value]
            data[parsed_line[key]] = parsed_line[value]

        else:
            # Save  func_result
            data[parsed_line[key]] = func_result

    # Close file
    flux.close()

    return data


def greater_than_0_int_filter(_, key: int=None, dictionary: dict = None) -> bool:
    """!
    @brief Test if the value in front of the key @p key inside @p dictionary can be an integer bigger than 0.
    Meant to be used inside  @ref extract_data_from_table as a "filter_"

    @param _ => Unused parameter. Exist due to how "filter_" in @extract_data_from_table works
    @param key : int = None => A key contained by @p dictionary.
    @param dictionary : dict = None => A dictionary that contain @p key

    @return bool => True : Yes ; False : No.

    """
    try:
        return int(dictionary[key]) > 0
    except ValueError:
        return False


def compile_gene_snp(genes_snp: dict[str, any], dict_of_number: dict[int, dict[str, int]] = None,
                     group: str = "None") -> dict[int, dict[str, int]]:
    """!
    @brief Extract the number of snp of all genes contained in @p genes_snp (snp = @p genes_snp 's values).
    Each number of snp is stored inside a new dictionary (@p dict_of_number 's keys). A dict is created in front
    of all keys (i.e. snp number). This dict contain the @p group (key) and the number of occurrences of this
    snp number for this key.

    @param genes_snp : dict[str,any] => A dictionary from @ref extract_data_from_table.
        e.g. {gene_1: number_of_snp_in_gene_1} =>  @code {"gene1": 3}  @endcode
        @note Values (number of snp) inside this dict are trans typed into integers.
    @param dict_of_number : dict[int, dict[str,int]] = None.
        A dict with the same structure as dictionaries returned by this function.
    @param group : str = "None" => Each occurrence of a number of snp increment the counter related to this group.

    @return dict[int, dict[str, int]] => A dictionary that store all number of snp found along with the number of
    occurrences {number_of_snp_1 : {group1: number_of_occurrences_of_number_of_snp_1_in_this_group}
    """
    dict_of_number = {} if dict_of_number is None else dict_of_number

    for _, snp_count in genes_snp.items():
        snp_count = int(snp_count)

        # Add this 'snp_count' to dict_of_number
        if snp_count not in dict_of_number:
            dict_of_number[snp_count] = {}

        # Add this 'group' to dict_of_number[snp_count]
        if group not in dict_of_number[snp_count]:
            dict_of_number[snp_count][group] = 0

        dict_of_number[snp_count][group] += 1

    return dict_of_number


def make_data_matrix(compiled_dict : dict[int, dict[str, int]], group: str, *groups: str,
                     simplified: bool = True, max_length: int = None) -> (list[list[int]], list[int]):
    """!
    @brief Use a compiled dict from @ref compile_gene_snp to create a matrix of value.
    Each lines represent one group (@p groups & @p group).
    Each line contain the number of genes that contain at least n genes

    @parblock
    @note Only groups specified in @p groups and @p group are extracted from @p compiled_dict
    @endparblock

    @parblock
    @note For below example we will consider that :
        - @code compiled_dict = {1: {"E. coli": 5},
                           2: {"E. coli": 3, "HIV": 4},
                           3: {"HIV": 2}
                           4: {"E. coli": 1, "HIV": 1}
                           } @endcode
    @endparblock

    @param compiled_dict : dict[int,dict[str,int]] => a compiled dict from @ref compile_gene_snp
    @param group : str => A group name (e.g. Species name : "E. coli")
    @param *groups : str => Same as @p group. Additional species name.
    @param simplified : bool = True => Do number of snp represented by 0 gene are deleted from the result ?
    @note This the presence / absence of a number is affected by other groups
        - with group="E. coli":
            - If True: @code ([[5, 3, 1]], [1, 2, 4]) @endcode
            - If False: @code ([[5, 3, 0, 1]], [1, 2, 3, 4]) @endcode
        - with group="E. coli" and groups= ("HIV", ):
            - If True: @code ([[5, 3, 0, 1], [0, 4, 2, 1]], [1, 2, 4])  @endcode
    @param max_length : int = None => Limit the length of each lines of the matrix. should be greater than 0. If not,
    max_length is ignored.

    @return (list[list[int]], list[int]) => Return a matrix and a list. Each lines of the matrix represent the
    number of genes of a species (group) that contain n snp : If the position 1 of a line is equal to 4, there is
    4 genes in the selected species that contain list[i] snp.
    The y axes can be labeled using @p group and @p groups (order in conserved) and  the x-axis is labeled by
    the list[int].

    @note For some return example, see @p simplified for return example
    """
    if max_length <= 0:
        max_length = None

    # Variables
    groups = [group, *groups]                       # Merge @p group and @p groups
    data = [list() for _ in range(0, len(groups))]  # Data matrix
    last_x_value = 0                                # Remember the last value
    sorted_x_values = sorted(compiled_dict)         # Snp size from compiled_dict sorted y size

    # Apply the @p max_length by reducing the size of "sorted_x_values"
    if max_length is not None and len(sorted_x_values) >= max_length:
        sorted_x_values = sorted_x_values[:max_length]

    # Fill data
    for x_values in sorted_x_values:
        group_at_this_position = compiled_dict[x_values]

        # missing_x_values is append at by each groups in order to extend the matrix.
        # the last value (pos -1) is always rewrote in the next loop
        missing_x_values = [0]
        if simplified is False:
            # When there is snp numbers represented by 0 genes, we add them using missing_x_values
            missing_x_values *= (x_values - last_x_value)

        # For each group, extend the matrix
        for i, group_name in enumerate(groups):
            data[i].extend(missing_x_values)

            # Store the value of this snp number
            if group_name in group_at_this_position:
                data[i][-1] = group_at_this_position[group_name]

        # Update last_x_value
        last_x_value = x_values

    # Return the matrix and the legend
    if simplified is True:
        return data, sorted_x_values

    else:
        return data, list(range(1, sorted_x_values[-1] + 1))


def generate_cumulative_list(list_of_numbers: list[int] or list[float], reversed_=False) -> list[int]:
    """!
    @brief Take a list of number and sum all values.
    @code
    [0, 5, 6, 1] => [0+5+6+1, 5+6+1, 6+1, 1] == [12, 12, 7, 1]
    @endcode

    @param list_of_numbers : list[int] or list[float] => A list that contain numbers.
    @param reversed_ = False => Do the accumulation start at the end and end at the beginning.

    @return list[int] => A list of number

    """

    cumulative_list = []
    tot = 0

    # Select the correct way to browse list_of_numbers
    if reversed_:
        index_range = list(range(-1, -(len(list_of_numbers) + 1), -1))
    else:
        index_range = range(0, len(list_of_numbers))

    # Fill cumulative_list
    for i in index_range:
        tot += list_of_numbers[i]
        cumulative_list.append(tot)

    # Reverse cumulative_list when needed
    if reversed_:
        cumulative_list.reverse()

    return cumulative_list


def export_list_in_tsv_as_rows(path: str, *rows, file_mode="w", encoding="UTF-8",
                               y_legend: list = None, x_legend: list = None):
    """!
    @brief Accept a number of list that represent rows of a tab and turn it intoo a tsv (flat file).

    @warning  Any "\t" or "\n" in rows' values will disrupt lines and / or columns

    Parameters :
        @param path : str => path (and name) of the file that will be written.
        @param *rows => A number of list
        @param file_mode = "w" => "w" or "a"
            - "w": if a file with the same path exist, old file is erased
            - "a": if a file with the same path exist, old file append new values
        @param encoding = "UTF-8" => File encoding
        @param y_legend : list = None => A list of item to be display in the first column
        @param x_legend : list = None => A list of item to be display at top of the file

    """
    # WARNING: \t and \n in rows can distributed lines / columns

    # Open file
    file_flux = open(path, mode=file_mode, encoding=encoding)

    if x_legend:
        # Add the legend
        rows = [x_legend, *rows]

        # Assure that y_legend is aligned with the correct line
        # (x_legend create a new line that shift y_legend)
        if y_legend is not None and len(y_legend) < len(rows):
            y_legend = ["", *y_legend]

    i = 0   # Initialise i for the last block of instruction
    for i, lines in enumerate(rows):

        # Add y_legend at the beginning of each lines
        if y_legend:
            if i < len(y_legend):   # Assure that y_legend can not create errors
                file_flux.write(y_legend[i])

            file_flux.write("\t")

        # Write line content
        for word in lines:
            file_flux.write(str(word) + "\t")

        # End line
        file_flux.write("\n")

    # Assure that y_legend is completely written
    if y_legend:
        while i < len(y_legend) - 1:
            file_flux.write(y_legend[i])
            file_flux.write("\t")
            i += 1

    # Close file
    file_flux.close()


def _chart_export(data: list[list[int]], show: bool = False, png: str = None, tsv: str = None, svg: str = None,
                  x_legend: list = None, y_legend: list = None):
    """!
    @brief Export the current chart.

    @note if data is the only argument, nothing happen.

    @param data : list[list[int]] => A matrix of values
    @param show : bool = False => Do current plot will be displayed ?
    @param png : str = None => Give a path to export the current plot as png
    @param tsv : str = None => Give a path to export @p data into a tsv.
    @param svg : str = None => Give a path to export the current plot as svg
    @param y_legend : list = None => When tsv is not none: A list of item to be display in the first column
                (@ref export_list_in_tsv_as_rows)
    @param x_legend : list = None => When tsv is not none: A list of item to be display at top of the file
                (@ref export_list_in_tsv_as_rows)

    """
    # Png export
    if png is not None:
        plt.savefig(png + ".png", format='png')

    # svg export (Scalable Vector Graphic )
    if svg is not None:
        plt.savefig(svg + ".svg", format='svg')

    # Export tsv (flat file)
    if tsv is not None:
        export_list_in_tsv_as_rows(tsv + ".tsv", *data, y_legend=y_legend, x_legend=x_legend)

    # show chart
    if show:
        plt.show()


def make_bar_char(data: list[int],
                  x_legend: list = None, x_legend_is_int: bool = True, y_legend_is_int: bool = True,
                  chart_name: str = None,
                  title: str = None, xlabel: str = None, ylabel: str = None,
                  show: bool = False, png: str = None, tsv: str = None, svg: str = None,
                  erase_last_plt: bool = True):
    """!
    @brief Create a @ref plt.bar using a bunch of argument.
    This function is made to assure a correct looking legend when used for snp.

    @param data : list[int] => A list of integer
    @param x_legend : list = None => Values used to legend the x-axis.
    @param x_legend_is_int : bool = True => Do x-axis represent oly integer
    @param y_legend_is_int : bool = True => Do y-axis represent oly integer
    @param chart_name : str = None => A name that will be used if tsv is not None to name a line.
    @param title : str = None => A title for this chart
    @param xlabel : str = None => A title for the x-axis
    @param ylabel : str = None => A title for the y-axis
    @param show : bool = False => Do current plot will be displayed ?
    @param png : str = None => Give a path to export the current plot as png
    @param tsv : str = None => Give a path to export @p data into a tsv.
    @param svg : str = None => Give a path to export the current plot as svg
    @param erase_last_plt : bool = True => If True, last plot is removed from @ref matplotlib.pyplot display
    """

    # Clear last plot
    if erase_last_plt:
        plt.close('all')
        plt.clf()
        plt.cla()

    # Add ticks
    if x_legend:
        plt.bar(x_legend, data, color='skyblue')
        plt.xticks(range(len(data)), x_legend)

    else:
        x_legend = list(range(1, len(data) + 1))
        plt.bar(x_legend, data, color='skyblue')

    # Assure that y-axis and x-axis use display only integer. (Just some plt magic)
    if y_legend_is_int:
        plt.gca().yaxis.set_major_locator(plt.MaxNLocator(integer=True))

    if x_legend_is_int:
        plt.gca().xaxis.set_major_locator(plt.MaxNLocator(integer=True))

    # Add labels
    plt.xlabel(xlabel)
    plt.ylabel(ylabel)
    plt.title(title)
    plt.gcf().canvas.manager.set_window_title(title)

    # export chart
    _chart_export(data=[data], x_legend=x_legend, tsv=tsv, png=png, show=show, svg=svg, y_legend=[chart_name])


def make_heatmap(data: list[list[int]],
                 x_legend: list = None, y_legend: list = None,
                 title: str = None, xlabel: str = None, ylabel: str = None,
                 show: bool = False, png: str = None, tsv: str = None, svg: str = None,
                 erase_last_plt: bool = True, contain_number: int = None,
                 test_color: str = "#a0a0a0", cmap: str = "jet",
                ):
    """!
    @brief Create a heatmap using a bunch of argument.
    This function is made to assure a correct looking legend when used for snp.

    @param data : list[int] => A list of integer
    @param x_legend : list = None => Values used to label the x-axis.
    @param y_legend : list = None => Values used to label the y-axis.
    @param title : str = None => A title for this chart
    @param xlabel : str = None => A title for the x-axis
    @param ylabel : str = None => A title for the y-axis
    @param show : bool = False => Do current plot will be displayed ?
    @param png : str = None => Give a path to export the current plot as png
    @param tsv : str = None => Give a path to export @p data into a tsv.
    @param svg : str = None => Give a path to export the current plot as svg
    @param erase_last_plt : bool = True => If True, last plot is removed from @ref matplotlib.pyplot memory
    @param contain_number : int = None => If greater or equal to 0, all cells will contain theirs values. if lower than 0,
    text in cell in automatically determined. If None, nothing happen.
    @param test_color : str = #a0a0a0 => HTML color code for text inside cells
        @note Only when contain_number is True
    @param cmap : str = jet => Color mod. supported values are 'Accent', 'Accent_r', 'Blues', 'Blues_r', 'BrBG',
    'BrBG_r', 'BuGn', 'BuGn_r', 'BuPu', 'BuPu_r', 'CMRmap', 'CMRmap_r', 'Dark2', 'Dark2_r', 'GnBu', 'GnBu_r',
    'Grays', 'Greens', 'Greens_r', 'Greys', 'Greys_r', 'OrRd', 'OrRd_r', 'Oranges', 'Oranges_r', 'PRGn', 'PRGn_r',
    'Paired', 'Paired_r', 'Pastel1', 'Pastel1_r', 'Pastel2', 'Pastel2_r', 'PiYG', 'PiYG_r', 'PuBu', 'PuBuGn',
    'PuBuGn_r', 'PuBu_r', 'PuOr', 'PuOr_r', 'PuRd', 'PuRd_r', 'Purples', 'Purples_r', 'RdBu', 'RdBu_r', 'RdGy',
    'RdGy_r', 'RdPu', 'RdPu_r', 'RdYlBu', 'RdYlBu_r', 'RdYlGn', 'RdYlGn_r', 'Reds', 'Reds_r', 'Set1', 'Set1_r', 'Set2',
     'Set2_r', 'Set3', 'Set3_r', 'Spectral', 'Spectral_r', 'Wistia', 'Wistia_r', 'YlGn', 'YlGnBu', 'YlGnBu_r', '
     YlGn_r', 'YlOrBr', 'YlOrBr_r', 'YlOrRd', 'YlOrRd_r', 'afmhot', 'afmhot_r', 'autumn', 'autumn_r', 'binary',
     'binary_r', 'bone', 'bone_r', 'brg', 'brg_r', 'bwr', 'bwr_r', 'cividis', 'cividis_r', 'cool', 'cool_r',
     'coolwarm', 'coolwarm_r', 'copper', 'copper_r', 'cubehelix', 'cubehelix_r', 'flag', 'flag_r', 'gist_earth',
     'gist_earth_r', 'gist_gray', 'gist_gray_r', 'gist_grey', 'gist_heat', 'gist_heat_r', 'gist_ncar', 'gist_ncar_r',
     'gist_rainbow', 'gist_rainbow_r', 'gist_stern', 'gist_stern_r', 'gist_yarg', 'gist_yarg_r', 'gist_yerg',
     'gnuplot', 'gnuplot2', 'gnuplot2_r', 'gnuplot_r', 'gray', 'gray_r', 'grey', 'hot', 'hot_r', 'hsv', 'hsv_r',
     'inferno', 'inferno_r', 'jet', 'jet_r', 'magma', 'magma_r', 'nipy_spectral', 'nipy_spectral_r', 'ocean',
     'ocean_r', 'pink', 'pink_r', 'plasma', 'plasma_r', 'prism', 'prism_r', 'rainbow', 'rainbow_r', 'seismic',
     'seismic_r', 'spring', 'spring_r', 'summer', 'summer_r', 'tab10', 'tab10_r', 'tab20', 'tab20_r', 'tab20b',
     'tab20b_r', 'tab20c', 'tab20c_r', 'terrain', 'terrain_r', 'turbo', 'turbo_r', 'twilight', 'twilight_r',
     'twilight_shifted', 'twilight_shifted_r', 'viridis', 'viridis_r', 'winter', 'winter_r'
    """

    # Clear the last plot
    if erase_last_plt:
        plt.clf()
        plt.cla()
        plt.close('all')

    # Number of rows and columns
    num_rows = len(data)
    num_cols = len(data[0])

    # Create heatmap
    fig_size = (num_cols + 1, max(num_rows + 1, 4))

    plt.figure(figsize=fig_size)
    plt.imshow(data, cmap=cmap, interpolation='nearest', vmin=1)

    # Add ticks
    if x_legend:
        plt.xticks(range(1, num_cols+1), x_legend)
    else:
        x_legend = [str(i) for i in range(1, num_cols + 1)]
        plt.xticks(range(num_cols), x_legend)

    if y_legend:
        plt.yticks(range(num_rows), y_legend)

    # Add labels
    plt.xlabel(xlabel)
    plt.ylabel(ylabel)
    plt.title(title)
    plt.gcf().canvas.manager.set_window_title(title)
    plt.gca().xaxis.set_major_locator(plt.MaxNLocator(integer=True))

    # Add color bar
    cbar = plt.colorbar()
    cbar.set_label('Number of genes')
    plt.gca().set_aspect('equal', adjustable='box')
    if contain_number is not None:
        # Add text labels inside heatmap cells
        units = ['', 'k', 'M', 'G', 'T', 'P']

        if contain_number < 0:
            font_size = min(12, min(fig_size) * 12)
        else:
            font_size = contain_number

        for i in range(len(data)):
            for j in range(len(data[0])):
                # pretreatment
                str_data = str(data[i][j])
                data_length = len(str_data)
                data_pos = data_length % 3
                data_units = data_length // 3

                # Round data at 3 significant numbers
                round_pos = max(data_length - 3, 0)
                round_pos *= -1
                str_data = str(round(data[i][j], round_pos))

                # Format units
                if data_units - 1 <= len(units):
                    # No unit
                    if data_units == 0:
                        str_data += "\n"    # Uniform text with other data

                    elif data_pos == 0:
                        str_data = f"{str_data[:3]}\n{units[data_units - 1]}"

                    else:
                        str_data = f"{str_data[:data_pos]},{str_data[data_pos: 3]}\n{units[data_units]}"

                else:
                    raise ValueError("Too many snp : " + str(data[i][j]))

                # Place text
                plt.text(j, i, f'{str_data}', ha='center', va='center', color=test_color, fontsize=font_size)

    _chart_export(data=data, y_legend=y_legend, x_legend=x_legend, tsv=tsv, png=png, show=show, svg=svg)


def _auto_getopts_simple_value(value_restriction: tuple[any, any], use_default=False) -> any:
    """!
    @brief Internal function used by  @ref auto_getopts.

    @param value_restriction : tuple[any, any] => A tuple of two value. (Default value, normal value).
    (False, True) when None
    @param use_default = False => Do the default value is returned

     @return any =>
        - True if value_restriction is None
        - Default value if @p value_restriction is True (@p value_restriction [1])
        - Normal value if @p value_restriction is False (@p value_restriction [0])
    """
    if value_restriction is None:
        value_restriction = (False, True)

    if use_default:
        return value_restriction[0]

    else:
        return value_restriction[1]


def _auto_getopts_complex_value(value_restriction, value, use_default=False) -> any:
    """!
    @brief Internal function used by  @ref auto_getopts. Use it to apply a number of restriction on a value.

    Parameters :
        @param value_restriction : tuple[any, callable] => > A tuple of two value. (Default value, normal value).
         (False, True) when None
         - if value_restriction[0] is callable : default = result of the function (no argument is given)
         - if value_restriction[0] is not callable : default = value_restriction[0]
         - if value_restriction[1] callable : is applied to @p value, the result is used as return value. If None
         @p value is returned with no change
        @param value => Value that can be returned. This value pass inside @p value_restriction [1]
        @param use_default = False => Do the default value is returned

     @return any => @p value transformed by  @p value_restriction [1]
    """
    if value_restriction is None:
        value_restriction = (None, None)

    if use_default:
        if callable(value_restriction[0]):
            return value_restriction[0]()
        else:
            return value_restriction[0]

    elif value_restriction[1] is None:
        return value
    else:
        return value_restriction[1](value)


def auto_getopts(argv: list[str], getopts_options: dict[None or str, None or tuple[any, any]],
                 *mandatory: str, help_message: str = None, force_default=True) -> dict:
    """!
    @brief Use @ref getopt.getopt to generate a dictionary for a function. All items can have default values and
    returned values can be trans typed (or passed inside a function)

    @param argv : list[str] => List of argument (strings). Usually sys.argv[1:].
    @note If the first values are not known option (option in @p getopts_options), the function will consider that
    those values correspond to the nth first option that require an argument in @p getopts_options.
    In below example, you can give two arguments. The first will be matched with "Alpha" and the last with "Beta".
    @code
    argv = ["5", "6"]
    getopts_options = {
        "Alpha=":               ("a:", None),
        "Beta=:                 ('b', (0, int)),
        "Gamma":                ("g", ("data/", str)),
        "Delta=":               ("d:", (0, lambda integer : int(integer) - 1)),
    }
    @endcode

    @param getopts_options : dict[str,None or tuple[any, any]] => dictionary that contain.
    This dict should have the following format : {complete_name: (shorten_name, (default_value, value_restriction) ) }
        - complete_name : Option called using --Complete_name. It's this name that is used to fill the returned dict.
        - shorten_name : Option called using -s.
        @note If an option require an argument, complete_name should end by an '=' AND shorten_name should end by a ':'.
        - (default_value, value_restriction):
            - Option that does not require an argument :
                - When None : None is replaced by (True, False)
                - default_value : The value used when this option is not used.
                - value_restriction : The value used when this option is used.

            - Option that require an argument :
                - None : Only for options in @p mandatory
                - default_value : The value used when this option is not used. (can be a callable)
                - value_restriction : None or a callable. Use it to turn your value in other type e.g. : int
    Example :
    @code
    getopts_options = {
        "Alpha=":               ("a:", None),
        "Beta":                 (None, None),
        "Gamma":                ("g", ("data/", str)),
        "Delta=":               ("d:", (0, lambda integer : int(integer) - 1)),
    }
    @endcode

    @param *mandatory : str => A list of option / argument that should be used at each time (e.g. file path in cut
    command)
    @param help_message : str = None => A message that will be displayed if the arguments are incorrect or if
    --help is used (any short key can be attributed to --help)
    @param force_default = True => All unspecified values are filled with theirs default value (see @p getopts_options)

    @note if a parameter is named "help" and that @p help_message is True,
    @return dict => list of parameter xtract from @p argv

    """

    option_dict = {}            # Will store options

    # Parse @p getopts_options
    short_opt = ""
    long_opt = []
    simple_keys = {}    # Keys that are supposed to have 2 values (True / False)
    complexe_keys = {}  # Keys that are supposed to have more than 2 values
    mandatory = set(mandatory)

    for long_keys, short_keys_and_value_restriction in getopts_options.items():
        # Unpack short_keys and filter when needed
        if isinstance(short_keys_and_value_restriction, tuple):
            short_keys, value_restriction = short_keys_and_value_restriction
        else:
            short_keys = short_keys_and_value_restriction
            value_restriction = None

        # Save long_keys and short_keys
        long_opt.append(long_keys)
        short_opt += short_keys

        # Associate short_keys and long_keys with theirs filters
        if short_keys[-1] == ":" and long_keys[-1] == "=":
            # Remove ":" and "="
            long_keys = long_keys[:-1]
            short_keys = short_keys[:-1]

            selected_dict = complexe_keys
            selected_default = _auto_getopts_complex_value
            default_args = (value_restriction, None, True)

        elif short_keys[-1] != ":" and long_keys[-1] != "=":
            # Keys with two values
            if value_restriction is None:
                value_restriction = (False, True)

            selected_dict = simple_keys
            selected_default = _auto_getopts_simple_value
            default_args = (value_restriction, True)

        # Verify short and long keys have no conflictual behaviors.
        else:
            # Conflict short key / long key
            if short_keys[-1] != ":":
                error_message = f"short key ('{short_keys}') ) do not asks for a value but long key do ('{long_keys}')."
            else:
                error_message = f"long key ('{long_keys}') do not asks for a value but short key do ('{short_keys}')."

            raise ValueError(f"Error in parameters definitions : " + error_message)

        # Do those keys already exists ?
        if "--" + long_keys in simple_keys or "--" + long_keys in complexe_keys:
            raise KeyError(f"{long_keys} long key is repeated.")

        if "-" + short_keys in simple_keys or "-" + short_keys in complexe_keys:
            raise KeyError(f"{short_keys} long key is repeated.")

        # Save options
        selected_dict["--" + long_keys] = (value_restriction, long_keys)
        selected_dict["-" + short_keys] = (value_restriction, long_keys)

        if force_default:
            option_dict[long_keys] = selected_default(*default_args)

    try:
        opts, unparsed = getopt.getopt(argv, short_opt, long_opt)

        if len(opts) == 0 and len(unparsed) >= 1:
            possible_keys = list(getopts_options.keys())
            i = 0

            while (i < len(possible_keys) and i < len(unparsed) and
                   possible_keys[i][-1] == "=" and unparsed[i][0] != "-"):
                opts.append(("--" + possible_keys[i][:-1], unparsed[i]))
                i += 1

            new_opts, unparsed = getopt.getopt(unparsed[i:], short_opt, long_opt)
            opts.extend(new_opts)

        if unparsed:
            raise KeyError(f"Can not understand all options : {' '.join(unparsed)} "
                           f"Understood :  {opts}")

    except getopt.GetoptError as GetE:
        raise GetE

    for option, value in opts:

        if option in simple_keys:
            # python3 main.py -rf --> [("-r", "f")].
            # That not what we want. We want  :
            # python3 main.py -rf -->[("-r", ""), ("-f", "")]:
            # In order to achieve that "value" at the end of opts

            if value:
                opts.extend([("-" + other_options, "") for other_options in value])

            # Apply filter
            value_restriction, option_name = simple_keys[option]
            option_dict[option_name] = _auto_getopts_simple_value(value_restriction)

        elif option in complexe_keys:
            value_restriction, option_name = complexe_keys[option]
            option_dict[option_name] = _auto_getopts_complex_value(value_restriction, value)

        else:
            raise KeyError("Unknown option, can not proceed : " + option)

        if option_name in mandatory:
            mandatory.remove(option_name)  # option_name comes from precedent if / else

    if mandatory:
        raise KeyError(f"{len(mandatory)} argument missing : {', '.join(mandatory)}")

    if help_message and "help" in option_dict:
        del option_dict["help"]

    return option_dict


def main(path: str, name_column: str, snp_column: str, file_separator: str = "\t",
         simplified: bool = True, max_length: int = None,
         output_path: str = "output", output_warning: bool = True, job_name: str = None,
         global_heatmap: bool = True, quantitative_barchart: bool = False, cumulative_barchart: bool = False,
         cumulative_heatmap: bool = False,
         tsv: bool = False, png: bool = False, show: bool = False, svg: bool = True,
         sort_by_name: bool = True,
         show_values: int = -1) -> int:
    """!
    @brief Create a number of chart related to snp analysis.

    As an example we will consider the following flatFile :
    | GeneName | GeneID | NumberOfSnp | GeneSize |
    |----------|--------|-------------|----------|
    | Gene1    | 123    | 5           | 1000     |
    | Gene2    | 456    | 10          | 2000     |

    @param path : str => Path that lead to a number of flatfile :
        - .json : {complete file path : Species name}
        - folder : Use file inside the folder (does not scan the folder recursively)

    @param name_column : str => Name of the column that contain a primary key e.g. GeneName, GeneID. If two line
    have the same "primary key", the last one will be used.
    @param snp_column : str => Name of the column that contain a count of snp e.g. NumberOfSnp
    @param file_separator : str = "\t" => The separator used in all flat file considered.
    @param simplified : bool = True =>  Do number of snp represented by 0 gene are deleted from the result
    @param max_length : int = None => Maximum length of each graph. keep the nth first result. Should be greater or
    equal to 1 otherwise, it would be ignored.
    @param output_path : str = "output" => Where graphs are saved.
    @param output_warning : bool = True => Ask confirmation when at least one file can be erased by this program.
    @param job_name : str = None => A name for this execution. (This creates a separated folder in
     @p output_path). Default = "unnamed"
    @param global_heatmap : bool = True => Do a heatmap that is the combination of all cumulative_heatmap is created
    @param quantitative_barchart : bool = False => Do this program create a barchart of snp distribution for each
    file (Number of gene that have n snp)
    @param cumulative_barchart : bool = False => Do this program create a barchart of snp distribution for each
    file ? (Number of gene that have AT LEAST n snp)
    @param cumulative_heatmap : bool = False => Do this program create a heatmap of snp distribution for each
    file ? (Number of gene that have AT LEAST n snp)
    @param tsv : bool = False => Do values used for chart are saved in a flatfile (.tsv)
    @param png : bool = False => Do created charts are saved as png
    @param show : bool = False => Do created charts are saved are shown
        @warning Each time a char is shown, the program stop. It will resume when the chart is closed.
    @param svg : bool = True => Do created charts are saved as svg (vectorize image)
    @param sort_by_name : bool = True => Do species are sorted in lexicographic order ?
    @param show_values : int = None => If greater or equal to 0, all cells will contain theirs values. if lower than 0,
    text in cell in automatically determined (can be ugly when show is True, but assure that the text is good in
    png and svg). If None, nothing happen.

    @return int => if greater than 0, an error occurred.
    - 1 job stopped by user
    - 2 no species found
    """
    parameters = locals().copy()

    # Set a default name for output_path
    if job_name is None or len(job_name) == 0:
        job_name = "job_name"

    # Assure that max_length is None or greater or equal to 1
    if max_length <= 0:
        max_length = None
    if show_values <= 0:
        show_values = -1

    # Assure that at least one thing will be generated
    if not (global_heatmap or quantitative_barchart or cumulative_barchart or cumulative_heatmap):
        global_heatmap = True
    # Assure that at least one thing will be generated
    if not (tsv or svg or png or show):
        png = True

    # ---- ---- Path Management ---- ---- #
    # Assure that @p output_path point to a folder
    if output_path is None or output_path == "":
        output_path = "output/"

    if output_path[-1] not in ("/", "\\"):
        output_path += "/"

    # Create @p output_path if needed
    if not os.path.exists(output_path):
        os.mkdir(output_path)

    # Load files
    if path[-5:] == ".json":
        with open(path, "r", encoding="utf-8") as js_flux:
            path_translation = dict(json.load(js_flux))
            list_of_files = path_translation
            file_path_prefix = ""

    else:
        # Assure that @p path point to a folder
        if path[-1] not in ("/", "\\"):
            file_path_prefix = path + "/"
        else:
            file_path_prefix = path

        list_of_files = os.listdir(file_path_prefix)
        path_translation = {}

    # Create file and directory path
    output_dir = output_path + "/" + job_name + "/"
    file_prefix = output_dir + job_name + "_"
    heatmap_prefix = file_prefix + "Heatmap"
    cumulative_prefix = file_prefix + "CumulativeBarchart_"
    quantitative_prefix = file_prefix + "QuantitativeBarchart_"

    # Generate output_dir
    if not os.path.exists(output_dir):
        os.mkdir(output_dir)

    # Verify that the folder is empty
    elif output_warning and os.listdir(output_dir):
        r_ = input(f"Folder is not empty. Some files can be lost. ({output_dir})\nContinue ? (y / n) :")

        if r_.lower() not in ("y", "ye", "yes", "t", "tr", "tru", "true"):
            print("Job stopped")
            return 1

    # ---- ---- Export Control ---- ---  "
    heat_png = f"{heatmap_prefix}" if png and global_heatmap else None
    heat_tsv = f"{heatmap_prefix}" if tsv and global_heatmap else None
    heat_svg = f"{heatmap_prefix}" if svg and global_heatmap else None
    heat_show = show and global_heatmap

    c_heat_png = f"{heatmap_prefix}" if png and cumulative_heatmap else None
    c_heat_tsv = f"{heatmap_prefix}" if tsv and cumulative_heatmap else None
    c_heat_svg = f"{heatmap_prefix}" if svg and cumulative_heatmap else None
    c_heat_show = show and cumulative_heatmap

    c_bar_png = f"{cumulative_prefix}" if png and cumulative_barchart else None
    c_bar_tsv = f"{cumulative_prefix}" if tsv and cumulative_barchart else None
    c_bar_svg = f"{cumulative_prefix}" if svg and cumulative_barchart else None
    c_bar_show = show and cumulative_barchart

    q_bar_png = f"{quantitative_prefix}" if png and quantitative_barchart else None
    q_bar_tsv = f"{quantitative_prefix}" if tsv and quantitative_barchart else None
    q_bar_svg = f"{quantitative_prefix}" if svg and quantitative_barchart else None
    q_bar_show = show and quantitative_barchart

    # ---- ---- Load files ---- ----
    all_snp = {}                        # {Number_of_snp, {File_name : Number_of_genes_with_this_number_of_snp}
    all_species = []                    # List all targeted files

    # process all files and load snp into all_species
    for files in list_of_files:
        if files[0] == ".":
            continue

        files_dict = extract_data_from_table(f"{file_path_prefix}{files}", key=name_column, value=snp_column,
                                             filter_=greater_than_0_int_filter, separator=file_separator)

        if files in path_translation:
            all_species.append(path_translation[files])
        else:
            all_species.append(files)

        all_snp = compile_gene_snp(files_dict, all_snp, group=all_species[-1])

    if sort_by_name:
        all_species.sort()

    # ---- ---- Matrix and chart generation ---- ----
    if not all_species:
        return 2

    data, x_legend = make_data_matrix(all_snp, *all_species, simplified=simplified, max_length=max_length)

    if len(x_legend) == x_legend[-1]:
        # Verify that x_legend is continue TODO:
        # if the legend is equivalent of the automatic one, we use the automatic legend
        # (e.g. when @p simplified is False or when there is no simplification),
        x_legend = None

    else:
        # When x_legend is not composed of str and @p simplified is True, BarChart have weird behaviour.
        x_legend = [str(item) for item in x_legend]

    for i in range(0, len(data)):
        line_name = all_species[i]

        # Make quantitative barchart
        if quantitative_barchart:
            make_bar_char(data[i], x_legend=x_legend, chart_name=line_name,
                          ylabel="Number of genes",
                          xlabel="Number of snp",
                          title=f"Number of snp per genes in {line_name}",
                          show=q_bar_show,
                          png=f"{q_bar_png}{line_name}" if q_bar_png else None,
                          tsv=f"{q_bar_tsv}{line_name}" if q_bar_tsv else None,
                          svg=f"{q_bar_svg}{line_name}" if q_bar_svg else None,
                          )

        # Replace the quantitative list by a cumulative list
        data[i] = generate_cumulative_list(data[i], reversed_=True)

        # Make cumulative Barchart
        if cumulative_barchart:
            make_bar_char(data[i],
                          show=c_bar_show, x_legend=x_legend, chart_name=line_name,
                          ylabel="Number of genes",
                          xlabel="Number of snp",
                          title=f"Number of genes with at least n snp in {line_name}",
                          png=f"{c_bar_png}{line_name}" if c_bar_png else None,
                          tsv=f"{c_bar_tsv}{line_name}" if c_bar_tsv else None,
                          svg=f"{c_bar_svg}{line_name}" if c_bar_svg else None,
                          )

    # Heatmap generation
    if cumulative_heatmap:
        for i, lines in enumerate(data):

            make_heatmap([lines], y_legend=[all_species[i]], x_legend=x_legend,
                         title=f"Number of genes with at least n SNP : {all_species[i]}",
                         xlabel="Number of snp",
                         ylabel="Species names",
                         show=c_heat_show,
                         png=f"{c_heat_png}_{all_species[i]}" if c_heat_png else None,
                         tsv=f"{c_heat_tsv}_{all_species[i]}" if c_heat_tsv else None,
                         svg=f"{c_heat_svg}_{all_species[i]}" if c_heat_svg else None,
                         contain_number=show_values)

    if global_heatmap:
        make_heatmap(data, y_legend=all_species, x_legend=x_legend,
                     title="Number of genes with at least n SNP",
                     xlabel="Number of snp",
                     ylabel="Species names",
                     show=heat_show,
                     png=heat_png + "_global" if heat_png else None,
                     tsv=heat_tsv + "_global" if heat_tsv else None,
                     svg=heat_svg + "_global" if heat_svg else None,
                     contain_number=show_values)

    return 0


def main_using_getopts(argv: list[str] or str):
    """@brief start @ref main.main using a string or sys.argv[1:]
    Example :
        - main_using_getopts(sys.argv[1:])
        - main_using_getopts("name_column snp_column tests/TargetedFiles.json -m 20 -gv -w -j Tests -e -1")

    @param argv : list[str] or str => List of argument (strings). Usually sys.argv[1:].
    @note If the first values are not known option (option in @p getopts_options), the function will consider that
    those values correspond to the nth first option that require an argument in @p getopts_options.
    In below example, you can give two arguments. The first will be matched with "Alpha" and the last with "Beta".
     @code
    argv = ["5", "6"]
    getopts_options = {
        "Alpha=":               ("a:", None),
        "Beta=:                 ('b', (0, int)),
        "Gamma":                ("g", ("data/", str)),
        "Delta=":               ("d:", (0, lambda integer : int(integer) - 1)),
    }
    @endcode
    @return int => exit code
    """

    if isinstance(argv, str):
        argv = argv.split(" ")

    try:
        main_params = auto_getopts(argv, __getopts__, "name_column", "snp_column",
                                   help_message=help_usage())

    except Exception as E:
        print("An error occurred :\n")
        print(E)
        print(help_usage())
        return 5

    exit_code = main(**main_params)
    if exit_code == 2:
        print("Not enough species.")

    return exit_code


if __name__ == "__main__":
    import sys
    exit(main_using_getopts(sys.argv[1:]))



