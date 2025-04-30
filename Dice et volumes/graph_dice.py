import pandas as pd              # Pour lire et manipuler les fichiers CSV
import numpy as np               # Pour les moyennes pondérées et statistiques
import matplotlib.pyplot as plt  # Pour générer le graphique
import os                        # Pour la gestion des chemins

# === Chemins vers les fichiers CSV contenant les scores de Dice par label ===
csv_rigide = "/mnt/c/Users/camil/Downloads/p3/sub-879509/dice_scores_by_label.csv"            # Résultats après recalage rigide+affine
csv_nonlin = "/mnt/c/Users/camil/Downloads/p3/sub-879509/dice_scores_nonlin_by_label.csv"     # Résultats après recalage non-linéaire

# === Chemin du fichier image de sortie ===
output_plot = "/mnt/c/Users/camil/Downloads/p3/sub-879509/comparaison_dice_scores_global.png"

# === Chargement des fichiers CSV dans des DataFrames ===
df_rig = pd.read_csv(csv_rigide)
df_nonlin = pd.read_csv(csv_nonlin)

# Liste des comparaisons temporelles disponibles (ex: 'ses-3mo←ses-6mo')
comparisons = df_rig["comparison"].unique()

data = []  # Liste pour stocker les résultats à tracer

# === Boucle sur chaque comparaison (ex: 6mo → 3mo) ===
for comp in comparisons:
    rig = df_rig[df_rig["comparison"] == comp]
    nonlin = df_nonlin[df_nonlin["comparison"] == comp]

    # Moyenne pondérée des scores de Dice, pondérée par le volume de référence
    dice_rig = np.average(rig["dice"], weights=rig["volume_ref"])
    dice_nonlin = np.average(nonlin["dice"], weights=nonlin["volume_ref"])

    # Écart-type non pondéré (variation de Dice entre labels)
    std_rig = np.std(rig["dice"])
    std_nonlin = np.std(nonlin["dice"])

    # Format propre pour l'affichage (ex: "10m → 3m")
    ses_fix, ses_mov = comp.split("←")
    label_clean = f"{ses_mov.replace('ses-', '').replace('mo', 'm')} → {ses_fix.replace('ses-', '').replace('mo', 'm')}"

    # Ajout au tableau des données
    data.append([label_clean, dice_rig, std_rig, dice_nonlin, std_nonlin])

# Conversion de la liste en DataFrame pour le graphique
df_plot = pd.DataFrame(data, columns=["Comparison", "Dice_rig", "Std_rig", "Dice_nonlin", "Std_nonlin"])

# === Création du graphique comparatif ===
x = np.arange(len(df_plot))  # Position des barres sur l'axe x
width = 0.35                 # Largeur des barres

plt.figure(figsize=(12, 6))  # Taille du graphique

# Barres pour rigid+affine
plt.bar(
    x - width/2,
    df_plot["Dice_rig"],
    width,
    yerr=df_plot["Std_rig"],
    capsize=5,
    label="Rigid+Affine"
)

# Barres pour recalage non-linéaire
plt.bar(
    x + width/2,
    df_plot["Dice_nonlin"],
    width,
    yerr=df_plot["Std_nonlin"],
    capsize=5,
    label="Non-linéaire"
)

# Paramètres de l'axe des x
plt.xticks(x, df_plot["Comparison"])

# Axe y : scores de Dice
plt.ylim(0, 1)
plt.xlabel("Période de recalage")
plt.ylabel("Dice score pondéré moyen")
plt.title("Comparaison des Dice scores pondérés\nRigid+Affine vs Non-linéaire")

# Affichage de la légende et d'une grille horizontale
plt.legend()
plt.grid(axis="y")

# Ajuste les marges pour éviter le chevauchement
plt.tight_layout()

# Sauvegarde et affichage du graphique
plt.savefig(output_plot)
plt.show()

# Confirmation dans le terminal
print(f"Graphique sauvegardé ici : {output_plot}")
