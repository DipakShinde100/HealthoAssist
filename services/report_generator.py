from fpdf import FPDF
from datetime import datetime
import os


class HealthoAssistPDF(FPDF):
    def header(self):
        self.set_font("Helvetica", "B", 15)
        self.cell(0, 10, "HealthoAssist - Patient Health Report", ln=True, align="C")
        self.set_font("Helvetica", "", 9)
        self.cell(0, 6, "AI-Powered Predictive Treatment & Medical Recommendation System", ln=True, align="C")
        self.ln(3)
        self.set_draw_color(100, 100, 200)
        self.set_line_width(0.5)
        self.line(10, self.get_y(), 200, self.get_y())
        self.ln(5)

    def footer(self):
        self.set_y(-15)
        self.set_font("Helvetica", "I", 8)
        self.set_text_color(128, 128, 128)
        self.cell(0, 10, f"Page {self.page_no()} | HealthoAssist | Disclaimer: For informational purposes only. Not a substitute for medical advice.", align="C")


class PDFReportGenerator:

    def _write_section_title(self, pdf, title):
        pdf.set_font("Helvetica", "B", 12)
        pdf.set_fill_color(102, 126, 234)
        pdf.set_text_color(255, 255, 255)
        pdf.set_x(10)
        pdf.cell(0, 9, "  " + title, ln=True, fill=True)
        pdf.set_text_color(0, 0, 0)
        pdf.ln(2)

    def _write_row(self, pdf, label, value):
        if not value or str(value).strip() in ["None", "nan", ""]:
            value = "N/A"
        pdf.set_font("Helvetica", "B", 10)
        pdf.set_x(12)
        pdf.cell(55, 7, str(label) + ":", border=0)
        pdf.set_font("Helvetica", "", 10)
        # Use write instead of multi_cell to avoid width issues
        pdf.set_x(67)
        remaining_width = 190 - 67
        pdf.cell(remaining_width, 7, str(value)[:120], ln=True)

    def _write_paragraph(self, pdf, text):
        if not text or str(text).strip() in ["None", "nan", ""]:
            text = "N/A"
        pdf.set_font("Helvetica", "", 10)
        pdf.set_x(12)
        # Split text into chunks to avoid width error
        text = str(text)
        max_chars = 110
        while len(text) > max_chars:
            chunk = text[:max_chars]
            pdf.cell(0, 7, chunk, ln=True)
            pdf.set_x(12)
            text = text[max_chars:]
        pdf.cell(0, 7, text, ln=True)
        pdf.ln(1)

    def _write_list_item(self, pdf, item):
        if not item:
            return
        item_text = "  -  " + str(item)
        pdf.set_font("Helvetica", "", 10)
        pdf.set_x(14)
        # Limit length to avoid overflow
        item_text = item_text[:120]
        pdf.cell(0, 7, item_text, ln=True)

    def generate_report(self, patient, consultation, recommendations, safety, history_summary, output_path):
        pdf = HealthoAssistPDF()
        pdf.set_auto_page_break(auto=True, margin=20)
        pdf.add_page()

        # Generated date
        pdf.set_font("Helvetica", "", 9)
        pdf.set_text_color(100, 100, 100)
        now = datetime.now().strftime("%d %B %Y, %I:%M %p")
        pdf.cell(0, 6, "Generated: " + now, ln=True, align="R")
        pdf.set_text_color(0, 0, 0)
        pdf.ln(3)

        # ==========================================
        # SECTION 1: Patient Details
        # ==========================================
        self._write_section_title(pdf, "Patient Information")

        name = str(patient.name) if patient.name else "N/A"
        email = str(patient.email) if patient.email else "N/A"
        gender = str(patient.gender) if patient.gender else "N/A"
        blood = str(patient.blood_group) if patient.blood_group else "N/A"
        phone = str(patient.phone) if patient.phone else "N/A"
        allergies = str(patient.allergies) if patient.allergies else "None"

        self._write_row(pdf, "Name", name)
        self._write_row(pdf, "Email", email)
        self._write_row(pdf, "Gender", gender)
        self._write_row(pdf, "Blood Group", blood)
        self._write_row(pdf, "Phone", phone)
        self._write_row(pdf, "Known Allergies", allergies)
        pdf.ln(4)

        # ==========================================
        # SECTION 2: Consultation Details
        # ==========================================
        self._write_section_title(pdf, "Consultation Details")

        cons_id = str(consultation.id)
        cons_date = consultation.consulted_at.strftime("%d-%m-%Y %H:%M:%S")
        disease = str(consultation.predicted_disease) if consultation.predicted_disease else "N/A"
        confidence = str(round((consultation.confidence_score or 0) * 100, 2)) + "%"
        referral = "Yes - Please consult a doctor" if consultation.referral_flag else "No"

        self._write_row(pdf, "Consultation ID", cons_id)
        self._write_row(pdf, "Date & Time", cons_date)
        self._write_row(pdf, "Predicted Disease", disease)
        self._write_row(pdf, "Confidence Score", confidence)
        self._write_row(pdf, "Referral Needed", referral)
        pdf.ln(4)

        # ==========================================
        # SECTION 3: Symptoms
        # ==========================================
        self._write_section_title(pdf, "Symptoms Entered")
        try:
            symptoms = consultation.get_symptoms_list()
        except Exception:
            symptoms = []

        if symptoms:
            symptoms_text = ", ".join([str(s) for s in symptoms])
            self._write_paragraph(pdf, symptoms_text)
        else:
            self._write_paragraph(pdf, "No symptoms recorded")
        pdf.ln(2)

        # ==========================================
        # SECTION 4: Disease Description
        # ==========================================
        self._write_section_title(pdf, "Disease Description")
        desc = recommendations.get("description", "No description available")
        self._write_paragraph(pdf, desc)
        pdf.ln(2)

        # ==========================================
        # SECTION 5: Medications
        # ==========================================
        self._write_section_title(pdf, "Recommended Medications")
        medications = recommendations.get("medications", [])
        if medications:
            for med in medications:
                self._write_list_item(pdf, med)
        else:
            self._write_paragraph(pdf, "No medications found")
        pdf.ln(2)

        # ==========================================
        # SECTION 6: Diet
        # ==========================================
        self._write_section_title(pdf, "Diet Recommendations")
        diet = recommendations.get("diet", [])
        if diet:
            for item in diet:
                self._write_list_item(pdf, item)
        else:
            self._write_paragraph(pdf, "No diet recommendations found")
        pdf.ln(2)

        # ==========================================
        # SECTION 7: Precautions
        # ==========================================
        self._write_section_title(pdf, "Precautions")
        precautions = recommendations.get("precautions", [])
        if precautions:
            for p in precautions:
                self._write_list_item(pdf, p)
        else:
            self._write_paragraph(pdf, "No precautions found")
        pdf.ln(2)

        # ==========================================
        # SECTION 8: Workout
        # ==========================================
        self._write_section_title(pdf, "Workout & Lifestyle Suggestions")
        workout = recommendations.get("workout", [])
        if workout:
            for w in workout:
                self._write_list_item(pdf, w)
        else:
            self._write_paragraph(pdf, "No workout recommendations found")
        pdf.ln(2)

        # ==========================================
        # SECTION 9: Safety Warnings
        # ==========================================
        self._write_section_title(pdf, "Safety Warnings")
        warnings = safety.get("warnings", [])
        if warnings:
            for w in warnings:
                warn_text = w.get("warning", "")
                self._write_list_item(pdf, warn_text)
        else:
            self._write_paragraph(pdf, "No safety warnings. All medications appear safe.")
        pdf.ln(2)

        # ==========================================
        # SECTION 10: Doctor Review
        # ==========================================
        self._write_section_title(pdf, "Doctor Review")
        reviewed = "Yes" if consultation.doctor_reviewed else "Not yet reviewed"
        doctor_note = str(consultation.doctor_note) if consultation.doctor_note else "No notes added"
        prescription = str(consultation.prescription) if consultation.prescription else "No prescription added"

        self._write_row(pdf, "Review Status", reviewed)
        self._write_row(pdf, "Doctor Note", doctor_note)
        self._write_row(pdf, "Prescription", prescription)
        pdf.ln(4)

        # ==========================================
        # SECTION 11: History Summary
        # ==========================================
        self._write_section_title(pdf, "Patient History Summary")
        total = str(history_summary.get("total_consultations", 0))
        past_diseases = history_summary.get("past_diseases", [])
        past_text = ", ".join([str(d) for d in past_diseases]) if past_diseases else "None"
        most_freq = str(history_summary.get("most_frequent_disease", "N/A"))
        last_date = str(history_summary.get("last_consultation_date", "N/A"))

        self._write_row(pdf, "Total Consultations", total)
        self._write_row(pdf, "Previous Diseases", past_text)
        self._write_row(pdf, "Most Frequent", most_freq)
        self._write_row(pdf, "Last Consultation", last_date)
        pdf.ln(5)

        # Save PDF
        pdf.output(output_path)
        print(f"PDF saved to: {output_path}")