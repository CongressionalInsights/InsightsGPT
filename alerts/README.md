This directory stores outputs from monitoring scripts, such as `scripts/monitor_keywords.py`. Typically, these are JSON files or reports highlighting documents or data entries that match specific flagged keywords or criteria.

## Keyword Management

The keyword monitoring script (`scripts/monitor_keywords.py`) identifies documents containing specific terms. You can customize the list of keywords:

**Default Method: Using `config/keywords.txt`**

*   To add or remove keywords, simply edit the `config/keywords.txt` file.
*   Each keyword should be on a new line.
*   The script will automatically use the keywords from this file by default.

**Alternative Methods (Command-Line)**

*   **Specify a different file**: You can use a different keywords file by running the script with the `--keywords-file /path/to/your/keywords.txt` argument.
*   **Direct keyword list**: You can provide keywords directly on the command line using the `--keywords` argument (e.g., `--keywords "term1" "term2"`). If used, this will override any keywords file.

Example `config/keywords.txt`:
```
regulation
policy
compliance
```
