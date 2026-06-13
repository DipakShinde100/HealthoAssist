from datetime import datetime


class HealthoChatbot:
    def __init__(self, recommender=None):
        self.recommender = recommender
        self.disease_list = []

        if recommender:
            self.disease_list = list(recommender.descriptions.keys())

    def get_response(self, user_message, user=None, consultation_history=None):
        message = user_message.strip().lower()

        # Empty message
        if not message:
            return "Please type something. I'm here to help!"

        # Greetings
        if any(word in message for word in ["hello", "hi", "hey", "good morning", "good evening", "good afternoon"]):
            name = user.name if user else "there"
            return f"Hello {name}! 👋 I'm HealthoAssist chatbot. I can help you with:\n\n" \
                   f"🔹 Disease information (e.g., 'What is diabetes?')\n" \
                   f"🔹 Medication info (e.g., 'Medicine for malaria')\n" \
                   f"🔹 Diet advice (e.g., 'Diet for typhoid')\n" \
                   f"🔹 Precautions (e.g., 'Precautions for dengue')\n" \
                   f"🔹 Your health history (e.g., 'My last consultation')\n\n" \
                   f"Just type your question!"

        # Help
        if any(word in message for word in ["help", "what can you do", "commands", "options"]):
            return "I can help you with:\n\n" \
                   "🔹 'What is [disease]?' — Disease description\n" \
                   "🔹 'Medicine for [disease]' — Medication list\n" \
                   "🔹 'Diet for [disease]' — Diet recommendations\n" \
                   "🔹 'Precautions for [disease]' — Precautions\n" \
                   "🔹 'Workout for [disease]' — Workout advice\n" \
                   "🔹 'My history' — Your consultation history\n" \
                   "🔹 'My last consultation' — Last consultation\n" \
                   "🔹 'List diseases' — All supported diseases\n\n" \
                   "Try asking something!"

        # Thank you
        if any(word in message for word in ["thank", "thanks", "thank you", "bye", "goodbye"]):
            return "You're welcome! 😊 Stay healthy. Remember, always consult a doctor for serious conditions. Take care!"

        # List all diseases
        if any(phrase in message for phrase in ["list disease", "all disease", "show disease", "supported disease", "which disease"]):
            if self.disease_list:
                disease_names = sorted(set(self.disease_list))
                disease_text = ", ".join([d.title() for d in disease_names[:20]])
                remaining = len(disease_names) - 20
                response = f"I know about {len(disease_names)} diseases:\n\n{disease_text}"
                if remaining > 0:
                    response += f"\n\n...and {remaining} more."
                response += "\n\nAsk me about any of these!"
                return response
            return "Disease database is not loaded yet."

        # My history / last consultation
        if any(phrase in message for phrase in ["my history", "my consultation", "past consultation", "previous consultation"]):
            if consultation_history and len(consultation_history) > 0:
                response = f"📋 You have {len(consultation_history)} consultation(s).\n\n"
                for i, c in enumerate(consultation_history[:5]):
                    date = c.consulted_at.strftime("%d %b %Y")
                    disease = c.predicted_disease or "Referral"
                    conf = round((c.confidence_score or 0) * 100, 1)
                    response += f"{i+1}. {date} — {disease} ({conf}%)\n"
                if len(consultation_history) > 5:
                    response += f"\n...and {len(consultation_history) - 5} more."
                response += "\n\nGo to History page for full details."
                return response
            return "You don't have any consultations yet. Go to 'Check Symptoms' to get your first prediction!"

        # Last consultation
        if any(phrase in message for phrase in ["last consultation", "latest consultation", "recent consultation"]):
            if consultation_history and len(consultation_history) > 0:
                c = consultation_history[0]
                date = c.consulted_at.strftime("%d %b %Y, %I:%M %p")
                disease = c.predicted_disease or "Referral"
                conf = round((c.confidence_score or 0) * 100, 1)
                symptoms = ", ".join(c.get_symptoms_list()[:5]) if c.get_symptoms_list() else "N/A"
                response = f"📋 Your last consultation:\n\n"
                response += f"📅 Date: {date}\n"
                response += f"🏥 Disease: {disease}\n"
                response += f"📊 Confidence: {conf}%\n"
                response += f"🩺 Symptoms: {symptoms}\n"
                reviewed = "Yes ✅" if c.doctor_reviewed else "Not yet ❌"
                response += f"👨‍⚕️ Doctor Reviewed: {reviewed}"
                return response
            return "No consultations found yet."

        # Find disease in message
        found_disease = self._find_disease(message)

        # What is [disease]
        if found_disease and any(word in message for word in ["what is", "what's", "tell me about", "explain", "describe", "about"]):
            return self._get_disease_info(found_disease)

        # Medicine for [disease]
        if found_disease and any(word in message for word in ["medicine", "medication", "drug", "tablet", "treatment", "cure"]):
            return self._get_medicine_info(found_disease)

        # Diet for [disease]
        if found_disease and any(word in message for word in ["diet", "food", "eat", "nutrition", "meal"]):
            return self._get_diet_info(found_disease)

        # Precautions for [disease]
        if found_disease and any(word in message for word in ["precaution", "care", "prevent", "avoid", "safety", "tip"]):
            return self._get_precaution_info(found_disease)

        # Workout for [disease]
        if found_disease and any(word in message for word in ["workout", "exercise", "physical", "activity", "yoga", "walk"]):
            return self._get_workout_info(found_disease)

        # If disease found but no specific query
        if found_disease:
            return self._get_disease_info(found_disease)

        # Symptoms related
        if any(word in message for word in ["symptom", "feeling", "i have", "i feel", "suffering"]):
            return "For symptom-based disease prediction, please go to the 'Check Symptoms' page.\n\n" \
                   "There you can select your symptoms and get an AI-powered prediction with medication, diet, and precaution recommendations."

        # Doctor related
        if any(word in message for word in ["doctor", "hospital", "emergency", "serious", "critical"]):
            return "⚠️ If you are experiencing serious or emergency symptoms, please:\n\n" \
                   "1. Call emergency services immediately\n" \
                   "2. Visit the nearest hospital\n" \
                   "3. Do NOT rely solely on AI predictions\n\n" \
                   "HealthoAssist is a support tool, not a replacement for professional medical care."

        # Default response
        return "I'm not sure I understand that. 🤔\n\n" \
               "Try asking:\n" \
               "🔹 'What is malaria?'\n" \
               "🔹 'Medicine for diabetes'\n" \
               "🔹 'Diet for typhoid'\n" \
               "🔹 'My last consultation'\n" \
               "🔹 'Help' — to see all options\n\n" \
               "Or go to 'Check Symptoms' for disease prediction."

    def _find_disease(self, message):
        if not self.recommender:
            return None

        message_lower = message.lower()

        # Try exact match first
        for disease in self.disease_list:
            if disease.lower() in message_lower:
                return disease

        # Try partial match
        message_words = message_lower.split()
        for disease in self.disease_list:
            disease_words = disease.lower().split()
            for dw in disease_words:
                if len(dw) > 3:
                    for mw in message_words:
                        if len(mw) > 3 and (dw in mw or mw in dw):
                            return disease

        return None

    def _get_disease_info(self, disease):
        if not self.recommender:
            return "Disease database not available."

        rec = self.recommender.get_recommendations(disease)
        desc = rec.get("description", "No description available")

        response = f"🏥 {disease.title()}\n\n"
        response += f"📝 {desc}\n\n"
        response += f"Want to know more? Ask:\n"
        response += f"🔹 'Medicine for {disease}'\n"
        response += f"🔹 'Diet for {disease}'\n"
        response += f"🔹 'Precautions for {disease}'"

        return response

    def _get_medicine_info(self, disease):
        if not self.recommender:
            return "Medicine database not available."

        rec = self.recommender.get_recommendations(disease)
        meds = rec.get("medications", [])

        if meds:
            med_list = "\n".join([f"  💊 {m}" for m in meds])
            response = f"💊 Medications for {disease.title()}:\n\n{med_list}\n\n"
            response += "⚠️ Always consult a doctor before taking any medication."
        else:
            response = f"No specific medications found for {disease.title()}."

        return response

    def _get_diet_info(self, disease):
        if not self.recommender:
            return "Diet database not available."

        rec = self.recommender.get_recommendations(disease)
        diet = rec.get("diet", [])

        if diet:
            diet_list = "\n".join([f"  🥗 {d}" for d in diet])
            response = f"🥗 Diet for {disease.title()}:\n\n{diet_list}"
        else:
            response = f"No specific diet recommendations found for {disease.title()}."

        return response

    def _get_precaution_info(self, disease):
        if not self.recommender:
            return "Precaution database not available."

        rec = self.recommender.get_recommendations(disease)
        precs = rec.get("precautions", [])

        if precs:
            prec_list = "\n".join([f"  ⚠️ {p}" for p in precs])
            response = f"⚠️ Precautions for {disease.title()}:\n\n{prec_list}"
        else:
            response = f"No specific precautions found for {disease.title()}."

        return response

    def _get_workout_info(self, disease):
        if not self.recommender:
            return "Workout database not available."

        rec = self.recommender.get_recommendations(disease)
        workout = rec.get("workout", [])

        if workout:
            workout_list = "\n".join([f"  🏃 {w}" for w in workout])
            response = f"🏃 Workout for {disease.title()}:\n\n{workout_list}"
        else:
            response = f"No specific workout recommendations found for {disease.title()}."

        return response