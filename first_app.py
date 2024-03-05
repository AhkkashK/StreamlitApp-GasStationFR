import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt



# Importation de la data :
@st.cache_resource
def load_data():

    # On charge
    df = pd.read_csv("prix-carburants.csv", sep=';')

    # On drop des colonnes

    c_drop = ["adresse", "horaires", "pop", "prix_maj", "prix_id", "epci_code", "reg_code", "dep_code",
              "com_code", "com_arm_code", "com_arm_name", "ville"]
    n_df = df.drop(columns=c_drop)

    n_df[['latitude', 'longitude']] = n_df['geom'].str.split(',', expand=True).astype(float)
    n_df = n_df.drop(columns=["geom"])

    # On drop les  lignes où il n'y a pas de valeur pour prix valeur et prix nom étant donné le gros volume de données
    n_df = n_df.dropna(subset=["prix_valeur", "prix_nom", "epci_name", "dep_name", "reg_name", "com_name"])

    # Création d'une nouvelle colonne (nombre de services):
    n_df['nombre_de_services'] = n_df['services_service'].str.count('//') + 1

    # Fonction pour extraire les services uniques
    def extract_unique_services(row):
        if isinstance(row, str): # on verifie si c'est bien un str
            return set(row.split('//'))
        return set()

    n_df['services_service'] = n_df['services_service'].apply(extract_unique_services)  # on apply dessus la fonctino qu'on vient de creer

    # une liste de tous les services uniques
    unique_services = set()  # set nous permet de pas avoir de doublons
    for services in n_df['services_service']:
        unique_services.update(services) # met à jour

    # Créez une colonne pour chaque service et indiquez si la station le propose ou non
    for service in unique_services:
        n_df[service] = n_df['services_service'].apply(lambda x: 1 if service in x else 0)  # Créer une colonne tout en remplissant

    return n_df


def pie_chart_distrib_prix(data):

   prix_nom_counts = data['prix_nom'].value_counts()
   fig = plt.figure()  # Créez une figure.
   plt.pie(prix_nom_counts, labels=prix_nom_counts.index, autopct='%1.1f%%', startangle=90)
   plt.axis('equal')
   plt.title('Distribution of Price Values by type of Fuel')
   return fig  # Retourne la figure.

def histogram_station_reg(data):

    region_counts = data['reg_name'].value_counts()
    fig = plt.figure()  # Créez une figure.
    plt.bar(region_counts.index, region_counts.values)
    plt.xlabel('Region')
    plt.ylabel('Number of Stations')
    plt.title('Distribution of Gas Stations by Region')
    plt.xticks(rotation=90)  #  pivoter à 90
    return fig

def price_scatter_reg(data):

    avg_price_by_region = data.groupby('reg_name')['prix_valeur'].mean()
    fig = plt.figure()  # Créez une figure.
    plt.scatter(avg_price_by_region.index, avg_price_by_region.values)
    plt.xlabel('Region')
    plt.ylabel('Average Price')
    plt.title('Average Price by Region')
    plt.xticks(rotation=90)
    return fig

def bar_chart_services_by_reg(data):

    avg_services_by_region = data.groupby('reg_name')['nombre_de_services'].mean()
    regions = avg_services_by_region.index
    avg_services = avg_services_by_region.values

    fig = plt.figure(figsize=(12, 6))
    plt.bar(regions, avg_services)
    plt.xlabel('Region')
    plt.ylabel('Average Number of Services')
    plt.title('Average Number of Services by Region')
    plt.xticks(rotation=90)
    return fig





def visualisation_plot_simple(data):

    st.title("Visualization of Data about Gas Stations in France")

    # Visualisation du pie chart prix /type carburant
    st.title("Distribution of the Price by type of Fuel")
    pie_chart_data = data
    pie_chart_fig = pie_chart_distrib_prix(pie_chart_data)
    st.pyplot(pie_chart_fig)

    # Visualisation de l'histogramme de la distribution des stations par région
    st.title("Distribution of Gas Stations by Region")
    histogram_station_data = data
    histogram_station_by_region_fig = histogram_station_reg(histogram_station_data)
    st.pyplot(histogram_station_by_region_fig)

    # Visualisation du scatter  du prix moyen par région
    st.title("Average Price by Region")
    price_scatter_data = data
    price_scatter_by_region_fig = price_scatter_reg(price_scatter_data)
    st.pyplot(price_scatter_by_region_fig)

    # Visualisation barres du nombre moyen de services par région
    st.title("Average number of Services by Region")
    services_bar_chart_data = data
    bar_chart_services_by_region_fig = bar_chart_services_by_reg(services_bar_chart_data)
    st.pyplot(bar_chart_services_by_region_fig)


def visualisation_stream(data):
    # Graphes streamlit

    # Bar chart

    # Les données que vous avez fournies
    st.title("Number of Gas Stations (24/24) in France")
    horaires_automate_counts = data['horaires_automate_24_24'].value_counts()
    st.bar_chart(horaires_automate_counts)

    # Scatter

    # Sélectionnezuniquement les données de la ville de Paris
    st.title('Distribution of the Price of Gazole in Paris')
    data_ile_de_france = data[data['com_name'] == 'Paris']
    st.scatter_chart(data_ile_de_france, y='cp', x='prix_valeur', use_container_width=True)# Permet de prendre la largeur de la page

    st.text('x: Price of Gazole | y: Postal Code ')  # précision


def interaction_stream(data):
    # Map france (selectbox)


    services_disponibles = data.columns[13:]  # Sélectionnez les colonnes de services
    st.title("Search for Gas Stations")

    # Sélection des services souhaités par l'utilisateur
    services_utilisateur = st.multiselect("Select which services you want :", services_disponibles)

    # Filtre les stations-service en fonction des services sélectionnés
    stations_filtrees = data[data[services_utilisateur].all(axis=1)]# Permet de verifier si c est true ou false avec .all(1), liste en comprehension

    # Créez une carte
    st.map(stations_filtrees, latitude='latitude', longitude='longitude')

    # Affichez les détails des stations-service filtrées
    st.write("Details of gas stations selected :")
    st.write(stations_filtrees)



    # Filtrage de la DataFrame en fonction des régions, départements, communes et type de carburant (radio et selectbox)
    st.title("Minimum Price of Fuel by Region,Departement,City and Type of Fuel")

    location_type = st.radio("Select type of localisation", ("Region", "Departement", "Commune")) # choix

    if location_type == "Region":
        locations = data["reg_name"].unique() # unique() permet de pas avoir des doublons
        selected_location = st.selectbox("Select a region", locations)
        filtered_data = data[data["reg_name"] == selected_location]
    elif location_type == "Departement":
        locations = data["dep_name"].unique()
        selected_location = st.selectbox("Select a departement", locations)
        filtered_data = data[data["dep_name"] == selected_location]
    else:
        locations = data["com_name"].unique()
        selected_location = st.selectbox("Select a city", locations)
        filtered_data = data[data["com_name"] == selected_location]

    # Filtrage en fonction du type de carburant
    fuel_types = data["prix_nom"].unique()
    selected_fuel = st.selectbox("Select the type of Fuel", fuel_types)
    filtered_data = filtered_data[filtered_data["prix_nom"] == selected_fuel]

    # Recherche du prix minimum
    min_price = filtered_data["prix_valeur"].min()

    # Affichage du prix minimum
    if len(filtered_data) > 0:
        st.write(f"Minimum Price of fuel {selected_fuel} in {selected_location} : {min_price} €/L")
    else:
        st.write(f"No data found for the fuel {selected_fuel} in {selected_location}.")




    # Sélection des services  (Side Bar)
    st.sidebar.title("Filter by Services")
    services = data.columns[13:]
    selected_services = st.sidebar.multiselect("Select services to display", services)

    #  radio pour région,  département ou  commune
    filter_option = st.sidebar.radio("Filter by", ["Region", "Departement", "City"])

    # Filtre région
    if filter_option == "Region":
        selected_region = st.sidebar.selectbox("Select a region", data["reg_name"].unique(), key="region_selector")
        if selected_region:
            filtered_data = data[data["reg_name"] == selected_region]

    # Filtre département
    if filter_option == "Departement":
        selected_department = st.sidebar.selectbox("Select a departement", data["dep_name"].unique(), key="department_selector")
        if selected_department:
            filtered_data = data[data["dep_name"] == selected_department]

    # Filtre commune
    if filter_option == "City":
        selected_commune = st.sidebar.selectbox("Select a city", data["com_name"].unique(), key="commune_selector")
        if selected_commune:
            filtered_data = data[data["com_name"] == selected_commune]

    # Filtrage des données
    filtered_data = filtered_data[filtered_data[selected_services].all(axis=1)]

    # Affichage de la liste des stations proposant les services sélectionnés
    st.title("Gas Stations that propose selected services")
    st.write(filtered_data[["id", "reg_name", "dep_name", "com_name", "latitude", "longitude"]])


def main():
    data = load_data()
    visualisation_plot_simple(data)
    visualisation_stream(data)
    interaction_stream(data)



main()

