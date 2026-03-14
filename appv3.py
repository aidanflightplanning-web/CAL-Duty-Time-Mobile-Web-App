import streamlit as st
import datetime
from fpdf import FPDF
import pandas as pd

def create_pdf(data):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", "B", 16)
    
    # Header
    pdf.cell(190, 10, "Crew Duty Log", ln=True, align="C")
    pdf.ln(10)
    
    # Flight Info
    pdf.set_font("Arial", "B", 12)
    pdf.cell(190, 10, "Flight Information", ln=True)
    pdf.set_font("Arial", "", 11)
    pdf.cell(95, 8, f"Flight Number: {data['flight_no']}", border=1)
    pdf.cell(95, 8, f"Date: {data['flight_date']}", border=1, ln=True)
    pdf.ln(5)
    
    # Duty Table
    pdf.set_font("Arial", "B", 12)
    pdf.cell(190, 10, "Duty Calculations", ln=True)
    pdf.set_font("Arial", "", 11)
    
    results = [
        ("Reporting Time", f"{data['report_time']} LT"),
        ("Sectors", str(data['sectors'])),
        ("Base Max Flight Duty Period", f"{data['base_fdp']} hrs"),
        ("Discretion Applied", data['discretion']),
        ("Flight Duty Period Expiry", f"{data['fdp_expiry']} LT"),
        ("Duty Ends (Post-flight)", f"{data['duty_ends']} LT")
    ]
    
    for label, value in results:
        pdf.cell(95, 8, label, border=1)
        pdf.cell(95, 8, value, border=1, ln=True)
        
    pdf.ln(10)
    pdf.set_font("Arial", "I", 8)
    pdf.multi_cell(190, 5, "Note: This log is for informational purposes. All times are Local Time (LT). Developed by Aidan Nerahoo.")
    
    return pdf.output(dest='S').encode('latin-1')

def calculate_crew_times():
    st.set_page_config(page_title="Crew Duty Tool", page_icon="✈️", layout="centered")
    
    st.markdown("""
        <style>
        [data-testid="stSidebar"] { display: none; }
        .main { background-color: #f8f9fa; }
        div.stButton > button:first-child {
            width: 100%;
            height: 3em;
            background-color: #004593;
            color: white;
            border-radius: 10px;
        }
        .stTextInput input { text-align: center; font-size: 1.2rem; }
        </style>
    """, unsafe_allow_html=True)

    st.title("✈️ Duty Calculator")
    st.caption("Developed by Aidan Nerahoo")

    with st.container():
        st.subheader("📋 Flight Details")
        f_col1, f_col2 = st.columns(2)
        with f_col1:
            flight_no = st.text_input("Flight #", value="BW600")
        with f_col2:
            flight_date = st.date_input("Date", datetime.date.today())

        st.markdown("---")
        
        st.subheader("🕒 Reporting & Sectors")
        st.info("💡 **Note:** Report Time must be entered in **Local Time**, **24-Hour Format** (HH:MM).")
        
        time_str = st.text_input("Report Time (HH:MM) LT", value="08:00")
        
        try:
            report_time = datetime.datetime.strptime(time_str, "%H:%M").time()
        except ValueError:
            st.error("Invalid format. Use HH:MM (e.g., 14:30)")
            report_time = datetime.time(8, 0)

        sectors = st.select_slider("Select Number of Sectors", options=[1,2,3,4,5,6,7,8], value=2)
        use_discretion = st.toggle("Apply Captain's Discretion (+1 hr)")

    st.markdown("---")

    # 2. Calculation Logic
    report_dt = datetime.datetime.combine(flight_date, report_time)
    
    hour = report_time.hour
    if 6 <= hour < 8:
        mapping = {1: 13.0, 2: 13.0, 3: 12.5, 4: 10.75, 5: 10.0, 6: 9.5, 7: 9.0, 8: 9.0}
    elif 8 <= hour < 13:
        mapping = {1: 14.0, 2: 12.5, 3: 13.5, 4: 11.75, 5: 11.0, 6: 10.5, 7: 10.0, 8: 9.0}
    elif 13 <= hour < 18:
        mapping = {1: 13.0, 2: 11.5, 3: 12.25, 4: 10.75, 5: 10.0, 6: 10.0, 7: 9.0, 8: 9.0}
    elif 18 <= hour < 22:
        mapping = {1: 12.5, 2: 12.25, 3: 10.75, 4: 9.75, 5: 9.0, 6: 9.0, 7: 9.0, 8: 9.0}
    else:
        mapping = {1: 11.0, 2: 10.75, 3: 9.5, 4: 9.0, 5: 9.0, 6: 9.0, 7: 9.0, 8: 9.0}

    base_fdp = mapping.get(sectors, 9.0)
    extension = 1.0 if use_discretion else 0.0
    fdp_expiry_dt = report_dt + datetime.timedelta(hours=base_fdp + extension)
    total_duty_dt = fdp_expiry_dt + datetime.timedelta(minutes=30)

    # 3. Output Section
    st.subheader("📊 Duty Limits")
    
    # Updated to always show Date and LT
    display_format = "%b %d, %H:%M LT"

    m1, m2 = st.columns(2)
    m1.metric("Flight Duty Period Expiry", fdp_expiry_dt.strftime(display_format))
    m2.metric("Duty End", total_duty_dt.strftime(display_format))

    summary_df = pd.DataFrame([
        {"Item": "Base Max Flight Duty Period", "Detail": f"{base_fdp} hrs"},
        {"Item": "Discretion", "Detail": "Applied (+1h)" if use_discretion else "No"},
        {"Item": "Total Sectors", "Detail": str(sectors)}
    ])
    st.dataframe(summary_df, use_container_width=True, hide_index=True)

    # 4. Export
    pdf_data = {
        "flight_no": flight_no,
        "flight_date": flight_date.strftime('%d-%b-%Y'),
        "report_time": report_time.strftime('%H:%M'),
        "sectors": sectors,
        "base_fdp": base_fdp,
        "discretion": "Yes (+1 hr)" if use_discretion else "No",
        "fdp_expiry": fdp_expiry_dt.strftime('%d-%b-%Y %H:%M'),
        "duty_ends": total_duty_dt.strftime('%d-%b-%Y %H:%M')
    }

    pdf_bytes = create_pdf(pdf_data)
    
    st.download_button(
        label="📥 SAVE DUTY LOG (PDF)",
        data=pdf_bytes,
        file_name=f"Duty_{flight_no}.pdf",
        mime="application/pdf"
    )

if __name__ == "__main__":
    calculate_crew_times()