# QuizBowlQuestionOptimization
Code for extracting most valuable + frequent initial parts of quizbowl questions for a particular query with AI.
Summarizes most frequent patterns early in the question so you can ANSWER FASTER! Also makes harder sample questions to practice with.
For now, more API based but may become web app in future.


SETUP STEPS:
0. Git setup\n
1. Clone this repo\n
   a. First, open a folder where you want this to be stored (recommended Desktop/folder inside Desktop)\n
   b. Then, open a terminal and navigate to the folder that you want this to be saved to (cd directory_path_here)\n
   c. Copy and paste this into your terminal: git clone https://github.com/JackWilson05/QuizBowlQuestionOptimization.git \n
2. Get a Gemini API key\n
   a. Create your Gemini key (see <a href="https://aistudio.google.com/welcome?utm_source=PMAX&utm_source=PMAX&utm_medium=display&utm_medium=display&utm_campaign=FY25-global-DR-pmax-1710442&utm_campaign=FY25-global-DR-pmax-1710442&utm_content=pmax&utm_content=pmax&gclsrc=aw.ds&gad_source=1&gad_campaignid=21521909442&gclid=Cj0KCQjwsPzHBhDCARIsALlWNG0b-XvStIn_QZnYx4JjBuI-LuMS6SKEAXa56KBUlUDt7pZ6p7n5_aQaAszmEALw_wcB" target="_blank">here</a> for more information)\n
   b. Create a file called .env in the same folder as the contents of this repo\n
   c. Add GEMINI_API_KEY="your_api_key_here" to the first line of the file and save it\n
4. Conda environment setup\n
   a. Install anaconda if you have not already (see ______ for more information)\n
   b. conda env create -f environment.yml -p ./qb_opt_ENV (this will create a conda environment inside your current directory at qb_opt_ENV)\n
   c. Activate the environment with: conda activate ./qb_opt_ENV \n
5. Run this (and enjoy!): python .\extract_and_filter.py to get your interactive questions \n
