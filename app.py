import google.generativeai as genai
import streamlit as st
from dotenv import load_dotenv
import os
import time
from fpdf import FPDF
import requests
from streamlit_folium import folium_static
import folium
import json
import smtplib

# Load environment variables from .env file
load_dotenv()

# Set Google Gemini API key
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))

# Streamlit app title
st.title("AI-Powered Travel Itinerary Planner")

# Help section
with st.expander("How to Use This App"):
    st.write("""
    1. Enter your destination, trip duration, budget, and preferences.
    2. Provide additional details like dietary preferences and walking tolerance.
    3. Click 'Generate Itinerary' to get a personalized travel plan.
    4. Save your itinerary as a PDF, email it, or share it on social media.
    """)

# User input section
st.header("Enter Your Travel Preferences")
destination = st.text_input("Destination (e.g., Paris):")
trip_duration = st.slider("Trip Duration (in days):", min_value=1, max_value=14, value=5)
budget = st.selectbox("Budget:", ["Low", "Moderate", "High"])
purpose = st.selectbox("Purpose of Trip:", ["Leisure", "Business", "Adventure"])
preferences = st.multiselect("Preferences:", ["History", "Food", "Nightlife", "Adventure", "Nature"])
language = st.selectbox("Select Language:", ["English", "French", "Spanish", "German"])

# Additional details
st.header("Additional Details")
dietary_preferences = st.text_input("Dietary Preferences (e.g., vegetarian, vegan):")
interests = st.text_input("Specific Interests (e.g., museums, hiking):")
walking_tolerance = st.selectbox("Walking Tolerance:", ["Low", "Moderate", "High"])
accommodation = st.selectbox("Accommodation Preference:", ["Budget", "Mid-range", "Luxury"])

# Handle vague or incomplete inputs
if "mix" in " ".join(preferences).lower() or "both" in " ".join(preferences).lower():
    st.write("It seems you want a mix of famous and offbeat places. Could you clarify the ratio? (e.g., 70% famous, 30% offbeat)")
    ratio = st.text_input("Ratio (e.g., 70-30):")
else:
    ratio = None

# Button to generate itinerary
if st.button("Generate Itinerary"):
    # Validate inputs
    if not destination:
        st.error("Please enter a destination.")
    elif not preferences:
        st.error("Please enter your preferences.")
    else:
        # Step 1: Construct the prompt based on user inputs
        if ratio:
            # If the user wants a mix of famous and offbeat places
            final_prompt = f"""
            Create a detailed {trip_duration}-day travel itinerary for {destination} with a {budget.lower()} budget.
            The purpose of the trip is {purpose.lower()}, and the user wants a mix of {ratio} famous and offbeat places.
            Additional details:
            - Dietary preferences: {dietary_preferences}
            - Specific interests: {interests}
            - Walking tolerance: {walking_tolerance}
            - Accommodation preference: {accommodation}
            Please provide a day-by-day itinerary with activities, dining options, and accommodation suggestions.
            """
        else:
            # Standard prompt for detailed inputs
            final_prompt = f"""
            Create a detailed {trip_duration}-day travel itinerary for {destination} with a {budget.lower()} budget.
            The purpose of the trip is {purpose.lower()}, and the user's preferences include {", ".join(preferences)}.
            Additional details:
            - Dietary preferences: {dietary_preferences}
            - Specific interests: {interests}
            - Walking tolerance: {walking_tolerance}
            - Accommodation preference: {accommodation}
            Please provide a day-by-day itinerary with activities, dining options, and accommodation suggestions.
            """

        # Step 2: Call Gemini API
        with st.spinner("Generating your personalized itinerary..."):
            try:
                model = genai.GenerativeModel('gemini-pro')
                response = model.generate_content(final_prompt)

                # Step 3: Display the generated itinerary
                st.header("Your Personalized Travel Itinerary")
                st.write(response.text)

                # Step 4: Add a map for the destination
                st.header("Map of Key Locations")
                if destination.lower() == "paris":
                    m = folium.Map(location=[48.8566, 2.3522], zoom_start=12)  # Coordinates for Paris
                    folium.Marker([48.8566, 2.3522], popup="Eiffel Tower").add_to(m)
                    folium_static(m)  # Display the map in the app

                # Step 5: Save itinerary as PDF
                def save_itinerary_as_pdf(itinerary, filename="itinerary.pdf"):
                    pdf = FPDF()
                    pdf.add_page()
                    pdf.set_font("Arial", size=12)
                    pdf.multi_cell(0, 10, itinerary)
                    pdf.output(filename)

                save_itinerary_as_pdf(response.text)
                st.success("Itinerary saved as PDF!")

                # Step 6: Budget Breakdown
                budget_prompt = f"""
                Based on a {budget.lower()} budget for {trip_duration} days in {destination}, provide a cost breakdown for:
                - Accommodation
                - Food
                - Activities
                """
                budget_response = model.generate_content(budget_prompt)
                st.header("Budget Breakdown")
                st.write(budget_response.text)

                # Step 7: Flight and Hotel Recommendations
                st.header("Flight and Hotel Recommendations")
                st.write("Here are some recommended flights and hotels for your trip:")
                st.write("- Flight: $500 round trip from New York to Paris")
                st.write("- Hotel: $100 per night at a mid-range hotel in Paris")

                # Step 8: Packing List
                packing_prompt = f"""
                Generate a packing list for a {trip_duration}-day trip to {destination} with a {budget.lower()} budget.
                Consider the activities mentioned in the itinerary.
                """
                packing_response = model.generate_content(packing_prompt)
                st.header("Packing List")
                st.write(packing_response.text)

                # Step 9: Save itinerary to history
                def save_itinerary_to_history(itinerary):
                    with open("history.json", "a") as f:
                        json.dump(itinerary, f)
                        f.write("\n")

                save_itinerary_to_history(response.text)

                # Step 10: Feedback System
                st.header("Feedback")
                rating = st.slider("Rate your experience (1-5):", min_value=1, max_value=5, value=3)
                feedback = st.text_area("Any additional feedback?")
                if st.button("Submit Feedback"):
                    st.success("Thank you for your feedback!")

                # Step 11: Email Itinerary
                def send_email(itinerary, recipient):
                    sender_email = "your_email@example.com"
                    sender_password = "your_email_password"
                    message = f"Subject: Your Travel Itinerary\n\n{itinerary}"
                    
                    with smtplib.SMTP("smtp.gmail.com", 587) as server:
                        server.starttls()
                        server.login(sender_email, sender_password)
                        server.sendmail(sender_email, recipient, message)

                email = st.text_input("Enter your email to receive the itinerary:")
                if st.button("Email Itinerary"):
                    send_email(response.text, email)
                    st.success("Itinerary sent to your email!")

                # Step 12: Social Media Sharing
                st.markdown("""
                ### Share Your Itinerary
                - [Twitter](https://twitter.com/intent/tweet?text=Check%20out%20my%20travel%20itinerary!)
                - [Facebook](https://www.facebook.com/sharer/sharer.php?u=your_app_url)
                - [WhatsApp](https://api.whatsapp.com/send?text=Check%20out%20my%20travel%20itinerary!)
                """)

                # Step 13: Personalized Recommendations
                recommendation_prompt = f"""
                Based on the user's preferences for {", ".join(preferences)}, suggest similar destinations or activities.
                """
                recommendation_response = model.generate_content(recommendation_prompt)
                st.header("Personalized Recommendations")
                st.write(recommendation_response.text)

                # Step 14: Real-Time Updates
                st.header("Real-Time Updates")
                st.write("Here are some real-time updates for your destination:")
                st.write("- The Louvre Museum is open until 9 PM today.")
                st.write("- There’s a special event at the Eiffel Tower this weekend.")

                # Step 15: Travel Challenges
                st.header("Travel Challenges")
                st.write("Complete these challenges during your trip:")
                st.write("- Visit 5 museums in Paris")
                st.write("- Try 3 local dishes")

                # Step 16: Points and Rewards
                st.header("Points and Rewards")
                st.write("Earn points for completing challenges and redeem them for discounts or perks.")

            except Exception as e:
                st.error(f"An error occurred: {e}. Please check your API key and try again.")