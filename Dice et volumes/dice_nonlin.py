import os                    # Pour la gestion des chemins de fichiers
import nibabel as nib        # Pour charger les fichiers .nii.gz contenant les segmentations
import numpy as np           # Pour les opérations matricielles
from scipy.ndimage import zoom  # Pour redimensionner les volumes en cas de mismatch de taille
import csv                   # Pour sauvegarder les résultats au format CSV

# Sujet traité
SUB = "sub-879509"

# Liste des paires à comparer (référence ← aligné)
pairs = [
    ("ses-3mo", "ses-6mo"),
    ("ses-3mo", "ses-10mo"),
    ("ses-6mo", "ses-10mo"),
]

# Répertoires d'entrée : segmentations de référence (après application de SyN) vs celles recalées
base_orig = f"/mnt/c/Users/camil/Downloads/p3/seg_nonlin_appliquees/{SUB}"  # segmentations transformées (référence)
base_aligned = f"/mnt/c/Users/camil/Downloads/p3/seg_nonlin/{SUB}"          # segmentations directement sur image déformée

# Fichiers de sortie (résultats Dice)
output_txt = f"/mnt/c/Users/camil/Downloads/p3/{SUB}/dice_scores_nonlin_weighted.txt"
output_csv = f"/mnt/c/Users/camil/Downloads/p3/{SUB}/dice_scores_nonlin_by_label.csv"

# Fonction pour calculer le Dice score entre deux masques binaires
def dice(seg1, seg2):
    intersection = np.logical_and(seg1, seg2).sum()
    return (2. * intersection) / (seg1.sum() + seg2.sum()) if (seg1.sum() + seg2.sum()) != 0 else 0

# Ouverture des fichiers de sortie texte et CSV
with open(output_txt, "w") as fout, open(output_csv, "w", newline="") as fcsv:
    writer = csv.writer(fcsv)
    writer.writerow(["comparison", "label", "dice", "volume_ref", "volume_aligned"])  # En-têtes du CSV

    fout.write("Dice scores non-linéaires (pondérés par volume du label)\n")
    fout.write("=========================================================\n")

    # Boucle sur chaque paire temporelle
    for ses_fix, ses_mov in pairs:
        folder = f"{ses_mov}_to_{ses_fix}"

        # Chemins vers les segmentations à comparer
        path_ref = os.path.join(base_orig, folder, f"seg_{SUB}_{folder}_nonlin.nii.gz")         # Référence = segmentation transformée
        path_aligned = os.path.join(base_aligned, folder, f"seg_{SUB}_{folder}_T1-T1.nii.gz")   # Segmentation directe sur image non-linéaire

        # Vérification de l’existence des fichiers
        if not os.path.exists(path_ref) or not os.path.exists(path_aligned):
            fout.write(f"Fichiers manquants pour {ses_fix} ← {ses_mov}\n")
            continue

        # Chargement des segmentations
        seg_ref = nib.load(path_ref).get_fdata()
        seg_aligned = nib.load(path_aligned).get_fdata()

        # Si les dimensions diffèrent, redimensionner la référence pour matcher l’alignée
        if seg_ref.shape != seg_aligned.shape:
            zoom_factors = np.array(seg_aligned.shape) / np.array(seg_ref.shape)
            seg_ref = zoom(seg_ref, zoom_factors, order=0)  # Nearest-neighbor (préserve les labels)

        # Si les formes ne sont toujours pas identiques, on skippe
        if seg_ref.shape != seg_aligned.shape:
            fout.write(f"Dimensions différentes pour {ses_fix} ← {ses_mov}\n")
            continue

        # Liste des labels présents dans la segmentation de référence
        labels = np.unique(seg_ref).astype(int)

        # Initialisation des statistiques
        weighted_dice = 0
        total_weight = 0
        all_dice = []
        all_weights = []

        print(f"\n {ses_fix} ← {ses_mov}")

        # Calcul du Dice pour chaque label
        for label in labels:
            if label == 0:
                continue  # On ignore le fond

            # Création des masques binaires pour le label
            mask_ref = seg_ref == label
            mask_aligned = seg_aligned == label

            # Calcul du Dice score
            dsc = dice(mask_ref, mask_aligned)
            weight = mask_ref.sum()  # Volume du label de référence

            # Enregistrement dans le CSV par label
            writer.writerow([f"{ses_fix}←{ses_mov}", label, round(dsc, 4), mask_ref.sum(), mask_aligned.sum()])

            # Accumulation des scores pour le Dice pondéré
            weighted_dice += dsc * weight
            total_weight += weight
            all_dice.append(dsc)
            all_weights.append(weight)

        # Calcul du Dice moyen pondéré et de l'écart-type
        if total_weight > 0:
            final_score = weighted_dice / total_weight
            var = sum(w * (x - final_score) ** 2 for x, w in zip(all_dice, all_weights)) / total_weight
            std = np.sqrt(var)
        else:
            final_score = 0
            std = 0

        # Écriture des résultats globaux dans le fichier texte
        fout.write(f"Dice {ses_fix} ← {ses_mov} (pondéré) : {final_score:.4f} ± {std:.4f}\n")
        print(f" Dice {ses_fix} ← {ses_mov} (pondéré) : {final_score:.4f} ± {std:.4f}")

# Fin du script
print(f"\n Résultats enregistrés dans :\n - {output_txt}\n - {output_csv}")
