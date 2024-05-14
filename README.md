# Snp HeatMap
The goal of this project is to create a number of chart 
related to snp (simple nucleotide polymorphism) analysis

Those charts are : 
- Quantitative bar chart (-q) : Show the number of gene (y) per number of snp (x)
- Cumulative bar chart (-c): Show the number of gene (y) that have at least n snp (x)
- Monoheatmap (-u): Cumulative bar chart but it's a heatmap
- global heatmap (-g): concatenation of all Monoheatmap

## Installation :
- Download
  1. Download Repository ("<> Code" button top right --> "Download zip")
  2. Unzip the Downloaded files


- Using linux terminal
  1. `git clone https://github.com/F-Marchal/SnpHeatMap.git`
  2. `cd SnpHeatMap`

see [Quick usage](#quick-usage-) and [Quick usage](#complete-usage-) in order to run main.py

## File format :
Files used by this script are expected to have the following pattern :

| Gene name / id | Other       | Snp counter |
|----------------|-------------|-------------|
| Gene1          | Other info1 | x           |
| Gene2          | Other info2 | y           |

- All files have to have the same headers 
- When a gene is present multiple times, only the last occurrence is used
- Snp counter should be integer. No dot ('.') or comma (',') are allowed in this cell.



## Usage :
Please read [File format](#file-format-) before using main.py and [Path to your files.](#path-to-your-files)

### Quick usage :
- Put your files inside the `data` folder
- run `python3 main.py [Gene name Column] [Snp column]`

### Complete usage :
`python3 main.py [Gene name Column] [Snp column] [Path to your files] [Options]`
This command will make a "global heatmap" for all your files in data
#### Arguments
- **Warning:** Arguments should always be before the parameters

##### Gene name Column
Name of the column that contain gene's names / ids in files. e.g. "Gene name / id" in [File format](#file-format-)

Can also be provided using parameters see [name_column](#--name_column-or--n)

##### Snp column
Name of the column that contain snp in files. e.g. "Snp counter" in [File format](#file-format-)

Can also be provided using parameters see [snp_column](#--snp_column-or--s)

##### Path to your files
Path toward your files can be give using two methods :
- Using a folder
  - All files inside the folder are used.
  - Names in the graph are file's names
  - Is the default option

- Using a json
  - This file should have the following format `{path_to_a_file: common_name}`
  - Names in the graph are `common_name`
  - If multiple path have the same `common_name` they will be considered as the same file.

Each files represent a species or a group of related individuals.

Can also be provided using parameters see [path](#--path-or--p)


#### Parameters
**Warning:** Parameters should always be afters the arguments 

##### --name_column or -n
This parameter must be followed by a string.

See [gene name Column](#gene-name-column)

##### --snp_column or -s
This parameter must be followed by a string.

See [snp column](#snp-column)

##### --path or -p
This parameter must be followed by a string that represent a path.

See [path to your files](#path-to-your-files)

##### --output_path -o
This parameter must be followed by a string that represent a path.
This parameter modify where charts and tsv are saved. 

Default = "./output"

##### --job_name -j
This parameter must be followed by a string that can be used as folder name.
This added a prefix to all files generated by this script.

Default = "Unnamed"

##### --max_length -m
This parameter must be followed by an integer. If this inger is lower than 0, max_length is ignored.
Limit the number of snp shown inside each graph.

Default = 20

##### --help -h
Display a help message.

Others parameters are ignored.

##### --output_warning -w
Disable the warning when you are about to generate files inside a non-empty folder.

##### --sort_by_name -r
Disable sort species by names in global heatmap.

##### --simplified -i
Ignore snp number represented by 0 genes. THIS MAY CREATE A DISCONTINUOUS X-AXIS

##### --global_heatmap -g
Generate a heatmap that represent all species.

##### --quantitative_barchart -q
Generate a barchart that represent snp distribution for each file (Number of gene that have n snp)

##### --cumulative_barchart -c
Generate a barchart that represent snp distribution for each file (Number of gene that **at least** n snp)

##### --cumulative_heatmap -u
Generate a heatmap for each file. This heatmap contain only one line.

##### --tsv -t
Generate a tsv for all generated charts.

##### --png -k
Generate a png for all generated charts.

##### --show -d
Show all generated charts during the execution. EACH CHARTS WILL STOP THE EXECUTION UNTIL IT IS CLOSED.

##### --svg -v
Generate a svg for all generated charts.

##### --show_values -e
Heatmap's cells contain theirs values.

