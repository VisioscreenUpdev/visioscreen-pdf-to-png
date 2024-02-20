import streamlit as st
from pdf2image import convert_from_bytes
import io
from PIL import Image
import PyPDF2


# Function to divide the image into four horizontal parts
def divide_image(image):
    width, height = image.size
    part_height = height // 4
    parts = [image.crop((0, part_height * i, width, part_height * (i + 1))) for i in range(4)]
    return parts


# Function to allow downloading of images
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
                    st.error(f"Numéro de page hors limite. Veuillez entrer un numéro de page entre 1 et {max_page_num}.")
                    return []
                pages.extend(range(start, min(end, max_page_num) + 1))
            else:
                page = int(part)
                if page > max_page_num or page < 1:
                    st.error(f"Numéro de page hors limite. Veuillez entrer un numéro de page entre 1 et {max_page_num}.")
                    return []
                pages.append(page)
        return list(set(pages))
    except ValueError:
        st.error("Veuillez entrer des numéros de pages ou des plages valides.")
        return []


def main():
    st.title("PDF to PNG Converter by Visioscreen")

    uploaded_pdf = st.file_uploader("Importez un fichier PDF", type="pdf")

    if uploaded_pdf is not None:
        # Read the PDF to determine the number of pages
        reader = PyPDF2.PdfReader(uploaded_pdf)
        max_page_num = len(reader.pages)
        pages_input = st.text_input(f"Entrez les numéros de page à traiter (par exemple, 1,3,5 ou 2-4). Page max : {max_page_num}",
                                    value="1")
        selected_pages = parse_pages_input(pages_input, max_page_num)

        if not selected_pages:
            # Stop further execution if there's an error in page selection
            return

        desired_width = st.number_input("Entrez la largeur souhaitée en pixels", value=600, step=100)
        desired_height = st.number_input("Entrez la hauteur souhaitée en pixels", value=800, step=100)

        if st.button("Traiter les pages sélectionnées"):
            uploaded_pdf.seek(0)  # Reset file pointer to the beginning of the file
            # Adjusting the convert_from_bytes function call
            images = convert_from_bytes(uploaded_pdf.read(), first_page=min(selected_pages),
                                        last_page=max(selected_pages))
            processed_pages = {page_num: img for page_num, img in
                               zip(range(min(selected_pages), max(selected_pages) + 1), images)}

            for page_number in selected_pages:
                if page_number in processed_pages:
                    original_img = processed_pages[page_number]

                    # Resize the image to the desired dimensions
                    resized_img = original_img.resize((desired_width, desired_height))
                    st.image(resized_img, caption=f"Page PDF redimensionnée {page_number} en tant qu'image")

                    # Divide the resized image into four parts
                    parts = divide_image(resized_img)

                    # Display and offer download links for each part
                    for j, part in enumerate(parts, start=1):
                        st.image(part, caption=f"Partie {j} de la Page {page_number}")
                        get_image_download_link(part, f"page_{page_number}_part_{j}",
                                                f"Télécharger Partie {j} de la Page {page_number}")


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
