

## ![code_rangers](uploads/63ad6cb90f781fc84d3156c1070830b3/code_rangers.png){:height="40px" width="40px"} # ***CODE RANGERS***

## **Team members:**
- Salahuddin Hassani
- Amgalanbaatar Khishigjargal
- Alkurdi Saifedin

## Game Description 
In this 2D top-down management game, you operate an African safari, balancing the care of wildlife, plant life, and infrastructure. You manage animals, hire rangers to protect against poachers, and build roads and facilities to attract tourists. The goal is to grow your safari by ensuring a healthy population of animals, increasing tourist visits, and maintaining your capital. The game features dynamic elements like a day-night cycle, random poacher attacks, and rangers that can be controlled to help secure the safari. Success is determined by meeting preset thresholds of visitors, animals, and capital over time.





#  📜  Requirements

<details>

<summary> 🔧 Functional</summary>

### 🟢 General (Can Be Done Anytime)
- Start a new game, selecting difficulty level.
- Adjust game speed (hour/day/week) or pause the game.
- Save and load game progress.
- Exit the game.

### 🌿 During the Game

#### Manage the Safari
- Purchase and place plants (trees, bushes, grass).
- Build water sources (ponds).
- Buy and introduce animals (herbivores and carnivores).
- Monitor and manage animal populations.

#### Control the Economy
- View and manage capital.
- Purchase jeeps for tourists.
- Build roads to connect safari entrance and exit.
- Set entry fees for tourists.
- Sell animals for profit.
- Hire and pay rangers to protect the safari and hunt specific animals.

#### Monitor Statistics & Gameplay
- View statistics on:
  - Number of visitors.
  - Number of herbivores and carnivores.
  - Financial balance (capital, income, and expenses).
- Track animal behavior (hunger, thirst, movement, reproduction).

#### Adjust Game Settings
- Change game speed (slow, normal, fast).
- Pause and resume the game.

### 🏗️ Buildable Objects

#### Plants and Water Areas
- *Bushes, trees, and grass*: Provide food for herbivores.
- *Ponds*: Supply water for animals.

#### Animals
- **Herbivores**:
  - Eat grass, bushes, and trees.
  - Require water to survive.
  - Move in groups.
- **Carnivores**:
  - Hunt herbivores for food.
  - Require water to survive.
  - Move in groups.

#### Jeeps and Roads
- **Jeeps**:
  - Can carry up to 4 tourists.
  - Follow random routes through the safari.
- **Roads**:
  - Must connect entrance and exit.
  - Allow jeeps to transport tourists.

### ✨ Additional Features

#### Minimap
- The map is larger than what is displayed on the main screen.
- Players can scroll through the map.
- A navigable minimap allows players to jump to specific locations.

#### Poachers
- Poachers randomly appear in the safari.
- Poachers shoot or capture animals and attempt to take them outside the safari.
- Poachers are only visible when near tourists or rangers.

#### Rangers
- Hired monthly for a salary.
- Can eliminate specific animals chosen by the player.
- Protect against poachers by eliminating them when nearby.
- Can be manually directed to chase poachers.
- Earn bounties for eliminating poachers.
- Poachers may retaliate if pursued.

#### Controllable Rangers
- Players can direct rangers to pursue specific poachers.
- Bounties are earned for eliminating poachers.
- Poachers may detect and retaliate against rangers.

#### Day-Night Cycle
- The game features a day-night cycle.
- At night:
  - Only plants, water, and roads are visible.
  - Animals are only visible if near tourists or rangers.
  - Players can purchase location chips (per animal) to track them at night.

### 🐾 Animals' Behavior
- Animals age over time and eventually die.
- Well-fed animals rest for hours before exploring.
- Hungry or thirsty animals actively search for food and water.
- Animals remember previously discovered food/water sources.
- Animals reproduce if conditions are met (adult members in the group).

### 🚙 Tourists & Revenue
- Tourists rent jeeps to explore the safari.
- The number of tourists depends on:
  - Animal population (more animals = more visitors).
  - Animal variety (more species = more attraction).
- Players earn money from:
  - Tourism (jeep rentals).
  - Selling animals.
  - Poacher bounties (if rangers eliminate poachers).

### 🏆 Winning & Losing Conditions

#### The game is won if:* 
For *3, 6, or 12 consecutive months* (depending on difficulty), the player maintains:
- A minimum number of visitors.
- A minimum number of herbivores and carnivores.
- A minimum capital balance.

#### The game is lost if:
- The player **goes bankrupt* (capital reaches 0).
- *All animals become extinct*.

</details>


<details>

<summary>⚙️ Non-Functional</summary>

### ⚡ Efficiency:

- The game should have minimal load on the processor, memory, and storage.
- It should provide a fast (under 0.5 seconds) response time to all user inputs, even on low-end computers.
- No network connection is required.

### 🛡️Reliability:

- The game should run without bugs or error messages under standard use.
- If incorrect input is provided by the player, an error message should be displayed, allowing the input to be corrected and reattempted.
- The game should not crash unexpectedly.
- No data storage is required, so no errors related to this will occur.

### 🔒 Security:

- Since no data is stored and the game does not connect to the internet, security is not a concern.

### 💻 Portability:

- The game should run on most personal computers, including Windows 8, 10, and 11, as a standalone application.
- It should not require installation and should be runnable after compilation.

### 🎮 Usability:

- The game should have an intuitive user interface that is easy to explore and learn for all players.
- No special instructions are required for the user to play the game.

### 🌱 Environmental:

- The game does not rely on any external software or services.

### ⏳ Operational:

- The game should typically run for 2-3 hours in a single session.
- The game is designed for single-player use, with no multiplayer capabilities.
- It should not require any special expertise to play.

### 🛠️ Development:

- The game will be developed using the Python programming language with Pygame.
- Version control will be managed via GitLab.
- The game will follow an object-oriented programming (OOP) paradigm.
- The code should be clean and maintainable.
- Unit testing will be conducted to ensure functionality and stability.
- Comprehensive documentation will be provided throughout the development process.

</details>



# 👤 User Story

<details>
  <summary>story</summary>

### 🟢 Game Start & Setup
| **As a Player** | **Given** (Precondition) | **When** (Action) | **Then** (Outcome) |
|---------------|-------------------------|------------------|------------------|
| I want to start a new game. | I launch the game and select a difficulty level. | I press the "Start Game" button. | A new safari map is generated, and I receive my starting capital. |
| I want to understand how to play. | I am new to the game. | I select the tutorial option. | A step-by-step guide teaches me how to manage my safari. |
| I want to buy an animal. | I have enough money and space in my safari. |	I purchase an animal from the shop. | The animal appears on the map and starts behaving naturally. |
| I want to sell an animal. | I own an animal. | I select it and choose the "Sell" option. | I receive money, and the animal leaves my safari. |
| I want animals to reproduce. | I have a group of adult animals. |	Conditions are met (e.g., age, food).	| New animals are born, increasing the population. |
| I want to buy a jeep. | I have enough money. | I purchase a jeep. | The jeep appears and can be used for tourism, generating revenue. |
| I want to build roads. | I have enough money. | I place road segments on the map. | The roads allow easier access for jeeps and visibility at night. |
| I want to hire a ranger. | I have enough money. | I purchase a ranger. | 	The ranger appears and follows assigned tasks (e.g., eliminating predators or poachers). |
| I want to eliminate a predator. | I have hired a ranger. | I command the ranger to target a predator. | The predator is removed, and I receive money. |
| I want to protect against poachers. | Poachers are present in my safari. | 	I assign a ranger to patrol or chase poachers. | The poacher is eliminated if the ranger is close enough, earning me a bounty. |
| I want to track an animal at night. |	It is nighttime, and I have animals.	| I purchase a location chip for an individual animal. | That animal remains visible at night. |
| I want to increase tourism. | I have animals, roads, and jeeps. | 	Tourists visit my safari. | I earn revenue based on the diversity and number of animals they see. |
| I want to survive poacher retaliation. | A poacher detects a ranger pursuing them. | The poacher retaliates against my ranger. | If my ranger is outnumbered or outgunned, they may be eliminated. |
| I want to navigate the map. | The safari is larger than the screen. | I scroll using the keyboard, mouse, or touchscreen. | The visible portion of the map updates, allowing me to explore different areas. |
| I want to use the minimap. | The minimap is enabled. | I click or tap on a location in the minimap. | The main view centers on that location for easier navigation. |

### 🎡 Tourism & Jeeps
| **As a Tourist** | **Given** (Precondition) | **When** (Action) | **Then** (Outcome) |
|---------------|-------------------------|------------------|------------------|
| I want to explore the safari. | The player has built roads and purchased jeeps. | I arrive at the safari entrance. | I rent a jeep and start my journey. |
| I want to enjoy my safari experience. | I am inside a jeep, exploring the safari. | I see a variety of animals. | My satisfaction increases, and the player earns revenue. |
| I want a better experience. | The player has money to invest. | The player purchases more animals and landscape elements. | I am happier, leading to higher revenue for the player. |

### 🥸 Poachers
| **As a Poacher** | **Given** (Precondition) | **When** (Action) | **Then** (Outcome) |
|---------------|-------------------------|------------------|------------------|
| I want to hunt animals illegally. | The game has been running for some time, and the safari has many animals. | I sneak into the park. | I remain hidden unless tourists or rangers are nearby. |
| I want to challenge the player. | The player's safari has rare or valuable animals. | I set traps or attempt to capture them. | If successful, the animal is removed, and the player loses resources. |

### 🏹 Rangers
| **As a Ranger** | **Given** (Precondition) | **When** (Action) | **Then** (Outcome) |
|---------------|-------------------------|------------------|------------------|
| I want to protect animals. | Poachers start appearing. | The player hires me. | I patrol the area and can eliminate poachers. |
| I want to control predator populations. | The safari has dangerous predators. | The player assigns me to eliminate a specific predator. | The predator is removed, and the player receives a reward. |

### 🛠️ Controllable Rangers
| **As a Player** | **Given** (Precondition) | **When** (Action) | **Then** (Outcome) |
|---------------|-------------------------|------------------|------------------|
| I want to directly control a ranger. | I have hired a ranger. | I select the ranger and take manual control. | I can move the ranger freely and take actions such as arresting poachers or monitoring animals. |
| I want to switch between rangers. | I have multiple rangers in my safari. | I select a different ranger to control. | Control shifts to the new ranger, and I can navigate and take actions. |
| I want to return to automatic patrol. | I am manually controlling a ranger. | I release control. | The ranger resumes patrolling on their own. |

### 🌃 Day-Night Cycle
| **As a Player** | **Given** (Precondition) | **When** (Action) | **Then** (Outcome) |
|---------------|-------------------------|------------------|------------------|
| I want the game to have a realistic day-night cycle. | The game is running. | Time progresses to night. | The map becomes darker, with only plants, water, and roads visible. |
| I want to track animals at night. | It is nighttime, and I have purchased tracking chips. | I activate the tracking chips. | I can see the locations of specific animals even in darkness. |

### 💰 Economy & Game Progression
| **As a Player** | **Given** (Precondition) | **When** (Action) | **Then** (Outcome) |
|---------------|-------------------------|------------------|------------------|
| I want to manage my funds carefully. | I start with a limited amount of capital. | I purchase animals, plants, roads, or jeeps. | My funds decrease, and I must balance spending with revenue generation. |
| I want to avoid bankruptcy. | My funds are running low. | I fail to generate enough income. | The game ends, and I lose. |
| I want to win the game. | I have maintained a successful safari for the required duration. | I meet the thresholds for visitors, animal populations, and capital. | The game declares me as the winner! 🎉 |

### 🏆 Winning & Losing Conditions  
| **As a Player** | **Given** (Precondition) | **When** (Action) | **Then** (Outcome) |  
|---------------|-------------------------|------------------|------------------|  
| I want to win the game. | I have played for a long time and managed my safari well. | I maintain a high number of visitors, herbivores, carnivores, and capital for the required duration. | I win the game, and a victory screen is displayed! 🎉 |  
| I want to avoid losing the game. | My resources are running low. | I fail to maintain enough money, animals, or visitors. | The game ends immediately, and I lose. 😢 |  
| I want a challenge based on difficulty. | I selected a difficulty level at the start. | The game progresses over months. | The required thresholds change based on my selected difficulty. |  

### 🚪 Game Exit & Replay  
| **As a Player** | **Given** (Precondition) | **When** (Action) | **Then** (Outcome) |  
|---------------|-------------------------|------------------|------------------|  
| I want to exit the game. | The game is running. | I press the "Exit" button. | The game closes, and progress is saved (if applicable). |  
| I want to restart after winning or losing. | I have reached the end of the game. | I select "Restart" or "New Game". | A fresh safari is generated, and I start over. |  
| I want to review my final stats. | The game has ended (win or lose). | I open the final summary screen. | I see detailed stats on my safari’s success and failures. |  

</details>







# Class diagram
<details>
<summary>🎭 Use Case Diagram</summary>
![use_case_diagram](uploads/e46e07bfb8253af9119d2b5587b236e4/use_case_diagram.drawio.png)
 

</details>


<details>
<summary>🏛️ MVC Diagram</summary>

<p align="center">
  ![MCV2](uploads/4e4d3ca30ad323f270f86e36d0270407/MCV2.png)
</p>

</details>


Some extra lines

<details>
<summary>🧩 High Level Class Diagram</summary>
 
![HighLevelClassDiagram2](uploads/2a20a845cbee0a194b3296f27b0a1ce5/HighLevelClassDiagram2.png)

#### Interaction Of Capital Class

<p align="center">
  <img src="uploads/d820f3e167e3ff4b05750245d707c406/softTech_2.png" width="550" height="550">
</p>

</details>


<details>
<summary>🔷 UML Diagram</summary>

 ![UML_Diagram_6](uploads/5b111eca1537bf4a9b59423708f43c47/UML_Diagram_6.png)

</details>


# UI Plan
<details>

<summary>📊 Diagram</summary>

## Start of the game
![Screenshot_2025-03-05_at_13.09.00](uploads/f602ea9d5f46210e4b498590a3704f44/Screenshot_2025-03-05_at_13.09.00.png)
## During the game
![Screenshot_2025-03-05_at_13.09.41](uploads/060cba3f3bc9ec2288945c645d74c756/Screenshot_2025-03-05_at_13.09.41.png)
## Menu
![Screenshot_2025-03-05_at_13.10.08](uploads/7ecde0e4b9538c06366aa5bda51fb6cf/Screenshot_2025-03-05_at_13.10.08.png)
## Settings to change game speed
![Screenshot_2025-03-11_at_20.27.35](uploads/dbfb5f41dfde08624fcf429b67919a27/Screenshot_2025-03-11_at_20.27.35.png)
## Store where user can buy and sell stuff
![Screenshot_2025-03-05_at_13.10.36](uploads/71f9fce090ceddd9c5b3c28e561aa390/Screenshot_2025-03-05_at_13.10.36.png)

</details># SafariPark
