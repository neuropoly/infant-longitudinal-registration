import os
import pandas as pd
import matplotlib.pyplot as plt

# Sujet analysé
SUB = "sub-879509"

# Sessions temporelles à analyser
sessions = ["ses-3mo", "ses-6mo", "ses-10mo"]

# Répertoires contenant les volumes pour chaque type de traitement
base_natif = f"/mnt/c/Users/camil/Downloads/p3/images_segmentees/{SUB}"                       # Volumes natifs
base_rigide = f"/mnt/c/Users/camil/Downloads/p3/images_rig_segmentees/{SUB}"             # Après recalage rigide
base_rigide_affine = f"/mnt/c/Users/camil/Downloads/p3/images_alignees_segmentees/{SUB}"      # Après recalage rigide + affine
base_nonlin = f"/mnt/c/Users/camil/Downloads/p3/seg_nonlin/{SUB}"                            # Après recalage non-linéaire

# Chemin du fichier CSV de sortie regroupant tous les volumes
output_csv = f"/mnt/c/Users/camil/Downloads/p3/{SUB}/comparaison_volumes_synthseg_quatre_niveaux.csv"

# === Définition des groupes anatomiques à analyser ===
group_mapping = {
    "cerebral white matter": ["left cerebral white matter", "right cerebral white matter"],
    "cerebral cortex": ["left cerebral cortex", "right cerebral cortex"],
    "lateral ventricle": ["left lateral ventricle", "right lateral ventricle"],
    "inferior lateral ventricle": ["left inferior lateral ventricle", "right inferior lateral ventricle"],
    "cerebellum white matter": ["left cerebellum white matter", "right cerebellum white matter"],
    "cerebellum cortex": ["left cerebellum cortex", "right cerebellum cortex"],
    "thalamus": ["left thalamus", "right thalamus"],
    "caudate": ["left caudate", "right caudate"],
    "putamen": ["left putamen", "right putamen"],
    "pallidum": ["left pallidum", "right pallidum"],
    "3rd ventricle": ["3rd ventricle"],
    "4th ventricle": ["4th ventricle"],
    "brain-stem": ["brain-stem"],
    "hippocampus": ["left hippocampus", "right hippocampus"],
    "amygdala": ["left amygdala", "right amygdala"],
    "CSF": ["csf"],
    "accumbens area": ["left accumbens area", "right accumbens area"],
    "ventral DC": ["left ventral DC", "right ventral DC"],
}

results = []

# === Boucle sur chaque session temporelle ===
for ses in sessions:
    print(f"Traitement de {ses}...")
    age = int(ses.split("-")[1].replace("mo", ""))  # Extrait l'âge en mois (ex: 6 pour ses-6mo)

    # Chemins vers les fichiers de volume pour chaque méthode
    vol_natif_path = os.path.join(base_natif, ses, "anat", f"volumes_{SUB}_{ses}.csv")
    vol_rig_path = os.path.join(base_rigide, f"{ses}_to_ses-3mo", f"volumes_rig_{SUB}_{ses}_to_ses-3mo_T1-T1_.csv")
    vol_rig_aff_path = os.path.join(base_rigide_affine, f"{ses}_to_ses-3mo", f"volumes_{SUB}_{ses}_to_ses-3mo_T1-T1_reg.csv")
    vol_nonlin_path = os.path.join(base_nonlin, f"{ses}_to_ses-3mo", f"volumes_{SUB}_{ses}_to_ses-3mo_T1-T1.csv")

    # Vérifie l'existence du volume natif
    if not os.path.exists(vol_natif_path):
        print(f"Volume natif manquant pour {ses}")
        continue

    # Chargement des fichiers CSV
    df_natif = pd.read_csv(vol_natif_path)
    df_rig = pd.read_csv(vol_rig_path) if os.path.exists(vol_rig_path) else None
    df_rig_aff = pd.read_csv(vol_rig_aff_path) if os.path.exists(vol_rig_aff_path) else None
    df_nonlin = pd.read_csv(vol_nonlin_path) if os.path.exists(vol_nonlin_path) else None

    # Calcul des volumes totaux par groupe anatomique
    for group, cols in group_mapping.items():
        vol_natif = df_natif[cols].sum(axis=1).values[0]

        if ses == "ses-3mo":
            # Pas de recalage à faire à 3 mois → on copie les volumes natifs
            vol_rig = vol_rig_aff = vol_nonlin = vol_natif
        else:
            vol_rig = df_rig[cols].sum(axis=1).values[0] if df_rig is not None else vol_natif
            vol_rig_aff = df_rig_aff[cols].sum(axis=1).values[0] if df_rig_aff is not None else vol_natif
            vol_nonlin = df_nonlin[cols].sum(axis=1).values[0] if df_nonlin is not None else vol_natif

        # Stockage des résultats pour chaque groupe
        results.append({
            "age": age,
            "group": group,
            "volume_natif_mm3": vol_natif,
            "volume_rigide_mm3": vol_rig,
            "volume_rigide_affine_mm3": vol_rig_aff,
            "volume_nonlin_mm3": vol_nonlin
        })

# === Sauvegarde du CSV global des volumes ===
df = pd.DataFrame(results)
df_grouped = df.groupby(["age", "group"])[["volume_natif_mm3", "volume_rigide_mm3", "volume_rigide_affine_mm3", "volume_nonlin_mm3"]].sum().reset_index()
df_grouped.to_csv(output_csv, index=False)
print(f"CSV sauvegardé : {output_csv}")

# === Identification des 4 structures les plus volumineuses ===
volume_moyens = df_grouped.groupby("group")[["volume_natif_mm3"]].mean().sort_values(by="volume_natif_mm3", ascending=False)
top4 = volume_moyens.head(4).index.tolist()
reste = [g for g in df_grouped["group"].unique() if g not in top4]

# === Définition des paramètres de visualisation ===
plot_config = [
    ("volume_natif_mm3", "Volumes SynthSeg natifs", "natif"),
    ("volume_rigide_mm3", "Volumes SynthSeg après recalage rigide", "rigide"),
    ("volume_rigide_affine_mm3", "Volumes SynthSeg après recalage rigide/affine", "rigide_affine"),
    ("volume_nonlin_mm3", "Volumes SynthSeg après recalage non-linéaire", "nonlineaire"),
]

# === Fonction pour tracer les volumes par groupe anatomique et méthode ===
def tracer_groupes(df, groupes, label, suffixe):
    for col, titre, nom in plot_config:
        plt.figure(figsize=(10, 6))
        for group in groupes:
            sous_df = df[df["group"] == group]
            plt.plot(sous_df["age"], sous_df[col], marker="o", label=group)
        plt.xlabel("Âge (mois)")
        plt.ylabel("Volume (mm³)")
        plt.title(f"{titre} - {label}")
        plt.legend(loc="upper left", bbox_to_anchor=(1.05, 1))
        plt.grid(True)
        plt.tight_layout()
        output_path = f"/mnt/c/Users/camil/Downloads/p3/{SUB}/volumes_{nom}_{suffixe}.png"
        plt.savefig(output_path)
        plt.close()

# Tracer pour les 4 structures les plus volumineuses
tracer_groupes(df_grouped, top4, "Structures les plus volumineuses", "top4")

# Tracer pour les autres structures
tracer_groupes(df_grouped, reste, "Autres structures", "reste")

print("Graphiques générés.")
