import os                    # Pour gérer les chemins de fichiers
import nibabel as nib        # Pour lire les fichiers d’imagerie médicale (.nii.gz)
import numpy as np           # Pour la manipulation des tableaux de données
from scipy.ndimage import zoom  # Pour redimensionner les images si leurs dimensions diffèrent
import csv                   # Pour écrire les résultats dans un fichier .csv

# Sujet analysé
SUB = "sub-879509"

# Liste des paires temporelles à comparer (fixe ← mobile)
pairs = [
    ("ses-3mo", "ses-6mo"),
    ("ses-3mo", "ses-10mo"),
    ("ses-6mo", "ses-10mo"),
]

# Répertoires contenant les segmentations :
base_orig = f"/mnt/c/Users/camil/Downloads/p3/images_alignees_segmentees/{SUB}"       # Segmentations des images alignées rigides et affine
base_aligned = f"/mnt/c/Users/camil/Downloads/p3/images_segmentees_alignees/{SUB}"    # Images segmentées puis alignées 

# Fichiers de sortie texte et CSV
output_txt = f"/mnt/c/Users/camil/Downloads/p3/{SUB}/dice_scores_by_label_weighted.txt"
output_csv = f"/mnt/c/Users/camil/Downloads/p3/{SUB}/dice_scores_by_label.csv"

# Fonction de calcul du Dice score entre deux masques booléens
def dice(seg1, seg2):
    intersection = np.logical_and(seg1, seg2).sum()
    return (2. * intersection) / (seg1.sum() + seg2.sum()) if (seg1.sum() + seg2.sum()) != 0 else 0

# Ouverture des fichiers de sortie
with open(output_txt, "w") as fout, open(output_csv, "w", newline="") as fcsv:
    writer = csv.writer(fcsv)
    writer.writerow(["comparison", "label", "dice", "volume_ref", "volume_aligned"])  # En-têtes du CSV

    fout.write(f"Dice scores (pondérés par volume des labels) pour {SUB}\n")
    fout.write("=============================================================\n")

    # Boucle sur chaque paire temporelle
    for ses_fix, ses_mov in pairs:
        folder = f"{ses_mov}_to_{ses_fix}"

        # Chemins des segmentations : référence et alignée
        path_ref = os.path.join(base_orig, folder, f"seg_{SUB}_{folder}_T1-T1_reg.nii.gz")
        path_aligned = os.path.join(base_aligned, folder, f"seg_{SUB}_{folder}_aligned.nii.gz")

        # Vérifie l’existence des fichiers requis
        if not os.path.exists(path_ref) or not os.path.exists(path_aligned):
            fout.write(f"Fichiers manquants pour {ses_fix} ← {ses_mov}\n")
            continue

        # Chargement des segmentations
        seg_ref = nib.load(path_ref).get_fdata()
        seg_aligned = nib.load(path_aligned).get_fdata()

        # Si les dimensions ne correspondent pas, on interpole la référence à la taille de l'alignée
        if seg_ref.shape != seg_aligned.shape:
            zoom_factors = np.array(seg_aligned.shape) / np.array(seg_ref.shape)
            seg_ref = zoom(seg_ref, zoom_factors, order=0)  # Nearest neighbor pour préserver les labels

        # Si toujours pas égal après resampling, on skippe
        if seg_ref.shape != seg_aligned.shape:
            fout.write(f"Dimensions différentes pour {ses_fix} ← {ses_mov}\n")
            continue

        # Extraction des labels présents dans la segmentation de référence
        labels = np.unique(seg_ref).astype(int)

        # Initialisation pour le Dice pondéré
        weighted_dice = 0
        total_weight = 0
        all_dice = []
        all_weights = []

        print(f"\n {ses_fix} ← {ses_mov}")

        # Calcul du Dice score pour chaque label (sauf fond = 0)
        for label in labels:
            if label == 0:
                continue

            mask_ref = seg_ref == label
            mask_aligned = seg_aligned == label
            dsc = dice(mask_ref, mask_aligned)
            weight = mask_ref.sum()  # Pondération selon le volume du label

            # Sauvegarde des résultats par label dans le CSV
            writer.writerow([f"{ses_fix}←{ses_mov}", label, round(dsc, 4), mask_ref.sum(), mask_aligned.sum()])

            # Stockage pour la moyenne pondérée et l'écart-type
            all_dice.append(dsc)
            all_weights.append(weight)
            weighted_dice += dsc * weight
            total_weight += weight

        # Calcul du Dice moyen pondéré et de son écart-type
        if total_weight > 0:
            final_score = weighted_dice / total_weight
            mean = final_score
            var = sum(w * (x - mean) ** 2 for x, w in zip(all_dice, all_weights)) / total_weight
            std = np.sqrt(var)
        else:
            final_score = 0
            std = 0

        # Écriture du score global dans le fichier texte
        fout.write(f"Dice {ses_fix} ← {ses_mov} (pondéré) : {final_score:.4f} ± {std:.4f}\n")
        print(f" Dice {ses_fix} ← {ses_mov} (pondéré) : {final_score:.4f} ± {std:.4f}")

# Confirmation finale
print(f"\n Résultats enregistrés dans :\n - {output_txt}\n - {output_csv}")
