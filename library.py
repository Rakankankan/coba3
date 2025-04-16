import streamlit as st
import pkg_resources

st.title("Daftar Library Python yang Terinstal")

# Mendapatkan daftar library yang terinstal
installed_packages = [(d.project_name, d.version) for d in pkg_resources.working_set]
installed_packages.sort()  # Mengurutkan berdasarkan nama

# Membuat header tabel
st.write("Berikut adalah daftar library yang terinstal beserta versinya:")

# Membuat tabel menggunakan Streamlit
st.table([{"Library": name, "Versi": version} for name, version in installed_packages])