# QuizBowlQuestionOptimization
Code for extracting most valuable + frequent initial parts of quizbowl questions for a particular query with AI.<br>
Summarizes most frequent patterns early in the question so you can ANSWER FASTER! Also makes harder sample questions to practice with.<br>
For now, more API based but may become web app in future.<br><br>


**SETUP STEPS**:<br>

0. Git setup (see <a href="https://docs.github.com/en/get-started/git-basics/set-up-git" target="_blank">here</a> if you haven't already set git up on your computer<br>
1. Clone this repo<br>
   a. First, open a folder where you want this to be stored (recommended Desktop/folder inside Desktop)<br>
   b. Then, open a terminal and navigate to the folder that you want this to be saved to (*cd directory_path_here*)<br>
   c. Copy and paste this into your terminal: *git clone https://github.com/JackWilson05/QuizBowlQuestionOptimization.git*<br>
2. Get a Gemini API key<br>
   a. Create your Gemini key (see <a href="https://aistudio.google.com/welcome?utm_source=PMAX&utm_source=PMAX&utm_medium=display&utm_medium=display&utm_campaign=FY25-global-DR-pmax-1710442&utm_campaign=FY25-global-DR-pmax-1710442&utm_content=pmax&utm_content=pmax&gclsrc=aw.ds&gad_source=1&gad_campaignid=21521909442&gclid=Cj0KCQjwsPzHBhDCARIsALlWNG0b-XvStIn_QZnYx4JjBuI-LuMS6SKEAXa56KBUlUDt7pZ6p7n5_aQaAszmEALw_wcB" target="_blank">here</a> for more information)<br>
   b. Create a file called *.env* in the same folder as the contents of this repo<br>
   c. Add *GEMINI_API_KEY="your_api_key_here"* to the first line of the file and save it<br>
4. Conda environment setup<br>
   a. Install anaconda if you have not already (see <a href="https://docs.conda.io/projects/conda/en/latest/user-guide/install/index.html" target="_blank">here</a> for more information)<br>
   b. Create environment with: *conda env create -f environment.yml -p ./qb_opt_ENV* (this will create a conda environment inside your current directory at qb_opt_ENV)<br>
   c. Activate the environment with: *conda activate ./qb_opt_ENV* <br>
5. Run this (and enjoy!): *python .\extract_and_filter.py* to get your interactive questions <br><br>


**HOW IT WORKS:**<br>
User query -> QBReader API Call -> Power Clue Extraction -> Gemini API Call -> Output (summaries, harder questions, and related terms)<br><br>

**EXAMPLE INPUT/OUTPUT:**<br>
<ins>Input:</ins><br>
   - Set: all<br>
   - Difficulty: 5,6 (Easy and Medium College)<br>
   - Category: 2 (Science)<br>
   - Query: Cnidaria<br>
   - Exact Match: y<br>
     
<ins>Output:</ins><br>
{<br>
    "overall_summary": "The user is asking about the phylum Cnidaria, which includes organisms like jellyfish and corals. The questions cover various aspects of this phylum, including their body forms (polyp and medusa), unique biological features like nematocysts and mesoglea, their life cycles (planula stage), and notable members like siphonophores and species that cause Irukandji syndrome. The data also touches on their ecological roles and evolutionary significance.",<br><br>
    "power_summary": "The most common and earliest occurring themes in the power questions revolve around specific organisms and their notable characteristics. This includes the longest known animal being a siphonophore, organisms causing Irukandji syndrome (and the eye structures involved), parasitic members causing diseases in salmon, and the presence of rhopalia for sensory functions. The ability to sleep without a brain and the concept of immortality due to stem cells are also highlighted early on. The fundamental biological features like mesoglea, hydrostatic skeleton, and the absence of a hard skeleton are also prominent.",<br><br>
    "hard_questions": \[
         "Name the phylum whose members are the first-known organisms capable of sleeping despite being brainless and possess specialized structures called rhopalia for movement and sensory input.",
        "Identify the phylum that contains the longest known animal, a siphonophore exceeding 40 meters, and also includes species responsible for the dangerous Irukandji syndrome.",
        "What phylum, characterized by a mesoglea layer and a hydrostatic skeleton, includes parasitic organisms that can cause whirling disease in salmon and genera like Haliclystus?"
    \],<br><br>
    "related_entities": \[
        "Jellyfish",
        "Corals",
        "Siphonophorae",
        "Irukandji syndrome",
        "Nematocysts"
    \]<br>
  }<br><br>
