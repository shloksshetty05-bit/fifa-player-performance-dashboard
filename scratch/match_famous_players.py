import pandas as pd
import os

processed_dir = "data/processed"
df_players = pd.read_csv(os.path.join(processed_dir, "players.csv"))

famous_candidates = [
    # Goalkeepers
    "Manuel Neuer", "Gianluigi Buffon", "Iker Casillas", "Guillermo Ochoa", 
    "Keylor Navas", "Thibaut Courtois", "Hugo Lloris", "Claudio Bravo", 
    "David de Gea", "Rui Patricio", "Alisson", "Ter Stegen", 
    "Yann Sommer", "Kasper Schmeichel", "Jordan Pickford", "Wojciech Szczesny", 
    "Fernando Muslera", "Tim Howard", "Emiliano Martinez",
    
    # Defenders
    "Sergio Ramos", "Gerard Pique", "Mats Hummels", "Jerome Boateng", 
    "Philipp Lahm", "Raphael Varane", "Thiago Silva", "Marquinhos", 
    "Dani Alves", "Marcelo", "Pepe", "Diego Godin", "Giorgio Chiellini", 
    "Leonardo Bonucci", "Vincent Kompany", "Toby Alderweireld", "Jan Vertonghen", 
    "Harry Maguire", "John Stones", "Kyle Walker", "Jordi Alba", 
    "Nicolas Otamendi", "Virgil van Dijk", "Daley Blind", "Dejan Lovren",
    
    # Midfielders
    "Luka Modric", "Toni Kroos", "Bastian Schweinsteiger", "Mesut Ozil", 
    "Andres Iniesta", "Sergio Busquets", "Cesc Fabregas", "Xabi Alonso", 
    "Paul Pogba", "N'Golo Kante", "Casemiro", "Fernandinho", 
    "Kevin De Bruyne", "Christian Eriksen", "Granit Xhaka", "Xherdan Shaqiri", 
    "Arturo Vidal", "Alexis Sanchez", "Angel Di Maria", "Ivan Perisic",
    
    # Forwards
    "Lionel Messi", "Cristiano Ronaldo", "Thomas Muller", "Kylian Mbappe", 
    "Neymar", "Harry Kane", "Luis Suarez", "Edinson Cavani", "Antoine Griezmann", 
    "Eden Hazard", "Robert Lewandowski", "Romelu Lukaku", "Miroslav Klose", 
    "David Villa", "Arjen Robben", "Robin van Persie", "Wesley Sneijder", 
    "Diego Forlan", "James Rodriguez", "Karim Benzema", "Zlatan Ibrahimovic"
]

matched_names = []
for name in famous_candidates:
    parts = name.split()
    # Simple pandas filter
    mask = pd.Series(True, index=df_players.index)
    for p in parts:
        mask = mask & df_players['name'].str.contains(p, case=False, na=False)
    matches = df_players[mask]
    if not matches.empty:
        matched_names.append(matches['name'].iloc[0])
    else:
        # Try last name
        matches = df_players[df_players['name'].str.contains(parts[-1], case=False, na=False)]
        if not matches.empty:
            matched_names.append(matches['name'].iloc[0])

print(f"Matched {len(matched_names)} names successfully:")
print(matched_names)
