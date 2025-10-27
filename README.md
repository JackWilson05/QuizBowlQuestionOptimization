# QuizBowlQuestionOptimization
Code for extracting most valuable + frequent initial parts of quizbowl questions for a particular query with AI.<br>
Summarizes most frequent patterns early in the question so you can ANSWER FASTER! Also makes harder sample questions to practice with.<br>
For now, more API based but may become web app in future.<br><br>


**SETUP STEPS**:<br>

0. Git setup (see <a href="https://docs.github.com/en/get-started/git-basics/set-up-git" target="_blank">here</a> or tutorials for <a href="https://www.youtube.com/watch?v=B4qsvQ5IqWk&pp=ygUSaG93IHRvIGluc3RhbGwgZ2l0" target="_blank">mac</a> or <a href="https://www.youtube.com/watch?v=t2-l3WvWvqg&pp=ygUSaG93IHRvIGluc3RhbGwgZ2l0" target="_blank">windows</a> if you haven't already set git up on your computer)<br>
1. Clone this repo<br>
   a. First, open a folder where you want this to be stored (recommended Desktop/folder inside Desktop)<br>
   b. Then, open a terminal and navigate to the folder that you want this to be saved to (*cd directory_path_here*)<br>
   c. Copy and paste this into your terminal: *git clone https://github.com/JackWilson05/QuizBowlQuestionOptimization.git*<br>
2. Get a Gemini API key<br>
   a. Create your Gemini key (see <a href="https://aistudio.google.com/welcome?utm_source=PMAX&utm_source=PMAX&utm_medium=display&utm_medium=display&utm_campaign=FY25-global-DR-pmax-1710442&utm_campaign=FY25-global-DR-pmax-1710442&utm_content=pmax&utm_content=pmax&gclsrc=aw.ds&gad_source=1&gad_campaignid=21521909442&gclid=Cj0KCQjwsPzHBhDCARIsALlWNG0b-XvStIn_QZnYx4JjBuI-LuMS6SKEAXa56KBUlUDt7pZ6p7n5_aQaAszmEALw_wcB" target="_blank">here</a> for more information or <a href="https://www.youtube.com/watch?v=o8iyrtQyrZM&pp=ygUeaG93IHRvIHNldCB1cCBhIGdlbWluaSBhcGkga2V5" target="_blank">here</a> for a tutorial)<br>
   b. Create a file called *.env* in the same folder as the contents of this repo<br>
   c. Add *GEMINI_API_KEY="your_api_key_here"* to the first line of the file and save it<br>
4. Conda environment setup<br>
   a. Install anaconda if you have not already (see <a href="https://docs.conda.io/projects/conda/en/latest/user-guide/install/index.html" target="_blank">here</a> for more information or <a href="https://www.youtube.com/watch?v=YJC6ldI3hWk&pp=ygUUaG93IHRvIGluc3RhbGwgY29uZGE%3D" target="_blank">here</a> for a tutorial)<br>
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
    "overall_summary": "Cnidaria is a phylum of aquatic invertebrates that includes corals, jellyfish, sea anemones, and hydras. These organisms are characterized by radial symmetry and possess specialized stinging cells called nematocysts, used for defense and capturing prey. Their body plan typically consists of two epithelial layers surrounding a jelly-like mesoglea, and they exhibit two main body forms: the sessile polyp and the free-swimming medusa. Some cnidarians, like the Irukandji jellyfish, can cause severe reactions in humans. Notably, certain members of this phylum, such as Turritopsis dohrnii, are considered biologically immortal due to their ability to revert to a polyp stage. The phylum also includes the colossal siphonophores, which are colonies of specialized zooids, some reaching impressive lengths.",<br><br>
    "power_summary": "Cnidarians are defined by the presence of nematocysts, explosive stinging organelles crucial for their survival. Their body structure is characterized by two layers of tissue surrounding a mesoglea, and they exhibit both polyp and medusa body forms. Some cnidarians, like those causing Irukandji syndrome, are particularly dangerous. Organisms within this phylum can also be identified by specialized structures like rhopalia for sensing and movement, and remarkably, some are capable of a form of biological immortality by reverting to a stem cell-like state. The extreme lengths of certain siphonophores, which are colonies of specialized individuals, also highlight unique adaptations within this phylum.",<br><br>
    "hard_questions": \[
         "What phylum contains organisms capable of biological immortality due to stem cell properties, and is known for its stinging nematocysts and radial symmetry?",
        "Which phylum's longest known animal is a siphonophore exceeding 40 meters, and whose members include species causing Irukandji syndrome and possess rhopalia for sensory functions?",
        "Name the invertebrate phylum whose body plan features mesoglea between two epithelial layers and includes species like corals and jellyfish, some of which are biologically immortal."
    \],<br><br>
    "related_entities": \[
        "Jellyfish",
        "Corals",
        "Sea Anemones",
        "Siphonophore",
        "Nematocysts"
    \]<br>
  }<br><br>
