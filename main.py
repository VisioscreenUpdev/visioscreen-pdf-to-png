import streamlit as st
from pdf2image import convert_from_bytes
import io
import PyPDF2


# Fonction pour diviser l'image en quatre parties horizontales et les redimensionner selon les dimensions souhaitées
def divide_and_resize_image(image, desired_width, desired_height):
    width, height = image.size
    part_height = height // 4
    parts_resized = []
    for i in range(4):
        # Découpage de chaque partie
        part = image.crop((0, part_height * i, width, part_height * (i + 1)))
        # Redimensionnement de chaque partie selon les dimensions souhaitées
        part_resized = part.resize((desired_width, desired_height))
        parts_resized.append(part_resized)
    return parts_resized


# Fonction pour permettre le téléchargement des images
def get_image_download_link(img, filename, text):
    buffered = io.BytesIO()
    img.save(buffered, format="PNG")
    st.download_button(text, buffered.getvalue(), f"{filename}.png", "image/png")


def parse_pages_input(pages_input, max_page_num):
    pages = []
    try:
        for part in pages_input.split(','):
            if '-' in part:
                start, end = map(int, part.split('-'))
                if start > max_page_num or end > max_page_num:
                    st.error(
                        f"Le numéro de page est hors limites. Veuillez entrer un numéro entre 1 et {max_page_num}.")
                    return []
                pages.extend(range(start, min(end, max_page_num) + 1))
            else:
                page = int(part)
                if page > max_page_num or page < 1:
                    st.error(
                        f"Le numéro de page est hors limites. Veuillez entrer un numéro entre 1 et {max_page_num}.")
                    return []
                pages.append(page)
        return list(set(pages))
    except ValueError:
        st.error("Veuillez entrer des numéros de pages valides ou des intervalles.")
        return []

from zipfile import ZipFile, ZIP_DEFLATED  # Assurez-vous que ZIP_DEFLATED est importé correctement

# Fonction pour créer un fichier ZIP des parties d'image et générer un lien de téléchargement
def create_download_zip(parts, prefix="pages"):
    zip_buffer = io.BytesIO()
    with ZipFile(zip_buffer, 'a') as zip_file:  # Suppression de l'argument compression pour éviter l'erreur
        for i, part in enumerate(parts, start=1):
            img_byte_arr = io.BytesIO()
            part.save(img_byte_arr, format='PNG')
            img_byte_arr = img_byte_arr.getvalue()
            zip_file.writestr(f"page_{prefix}_part_{i}.png", img_byte_arr, compress_type=ZIP_DEFLATED)  # Spécifiez ici la méthode de compression
    zip_buffer.seek(0)
    return zip_buffer

def main():
    st.title("Convertisseur PDF en PNG et redimensionnement")
    st.subheader("By Visioscreen")

    uploaded_pdf = st.file_uploader("Téléchargez un fichier PDF", type="pdf")

    if uploaded_pdf is not None:
        reader = PyPDF2.PdfReader(uploaded_pdf)
        max_page_num = len(reader.pages)
        pages_input = st.text_input(
            f"Entrez les numéros de pages à traiter (par exemple, 1,3,5 ou 2-4). Page max : {max_page_num}", value="1")
        selected_pages = parse_pages_input(pages_input, max_page_num)

        if not selected_pages:
            return

        desired_width = st.number_input("Entrez la largeur souhaitée en pixels pour chaque partie", value=600, step=100)
        desired_height = st.number_input("Entrez la hauteur souhaitée en pixels pour chaque partie", value=800,
                                         step=100)
        if st.button("Traiter toutes les pages"):
            uploaded_pdf.seek(0)
            images = convert_from_bytes(uploaded_pdf.read())
            all_parts = []
            for page_number, image in enumerate(images, start=1):
                parts_resized = divide_and_resize_image(image, desired_width, desired_height)
                all_parts.extend(parts_resized)

            # Créer un fichier ZIP avec toutes les parties redimensionnées
            zip_buffer = create_download_zip(all_parts, "all_pages")
            st.download_button(label="Télécharger toutes les images en ZIP",
                               data=zip_buffer,
                               file_name="all_pages_parts.zip",
                               mime="application/zip")

        if st.button("Traiter les pages sélectionnées une a une "):
            uploaded_pdf.seek(0)
            images = convert_from_bytes(uploaded_pdf.read(), first_page=min(selected_pages),
                                        last_page=max(selected_pages))
            processed_pages = {page_num: img for page_num, img in
                               zip(range(min(selected_pages), max(selected_pages) + 1), images)}

            for page_number in selected_pages:
                if page_number in processed_pages:
                    original_img = processed_pages[page_number]

                    # Division et redimensionnement de l'image
                    parts_resized = divide_and_resize_image(original_img, desired_width, desired_height)

                    # Affichage et mise à disposition des liens de téléchargement pour chaque partie
                    for j, part in enumerate(parts_resized, start=1):
                        st.image(part, caption=f"Partie {j} de la page {page_number}")
                        get_image_download_link(part, f"page_{page_number}_part_{j}",
                                                f"Télécharger la partie {j} de la page {page_number}")


if __name__ == "__main__":
    st.markdown("""
                    <style>
                    .stActionButton {visibility: hidden;}
                    /* Hide the Streamlit footer */
                    .reportview-container .main footer {visibility: hidden;}
                    /* Additionally, hide Streamlit's hamburger menu - optional */
                    .sidebar .sidebar-content {visibility: hidden;}
                    </style>
                    """, unsafe_allow_html=True)
    main()
