import customtkinter as ctk
import PyPDF2
import re
import tkinter as tk
import textwrap
from tkinter import filedialog
from PIL import Image, ImageTk

def wrap_text(text, width=80):
    """Wrap text to fit in specified width."""
    return "\n".join(textwrap.wrap(text, width=width))

class QuizApp:
    def __init__(self, root):
        self.root = root
        self.root.title("PDF Quiz Application")
        self.root.geometry("800x600")
        
        # Set appearance mode and theme
        ctk.set_appearance_mode("System")
        ctk.set_default_color_theme("blue")
        
        # Initialize variables
        self.questions = []
        self.current_question_index = 0
        self.user_answers = {}
        self.score = 0
        
        # Create main frame
        self.main_frame = ctk.CTkFrame(self.root)
        self.main_frame.pack(fill="both", expand=True, padx=20, pady=20)
        
        # Create upload frame
        self.upload_frame = ctk.CTkFrame(self.main_frame)
        self.upload_frame.pack(fill="x", padx=10, pady=10)
        
        self.upload_label = ctk.CTkLabel(self.upload_frame, text="Select a PDF file with quiz questions and answers:")
        self.upload_label.pack(side="left", padx=10, pady=10)
        
        self.upload_button = ctk.CTkButton(self.upload_frame, text="Upload PDF", command=self.upload_pdf)
        self.upload_button.pack(side="right", padx=10, pady=10)
        
        # Create question frame
        self.question_frame = ctk.CTkFrame(self.main_frame)
        self.question_frame.pack(fill="both", expand=True, padx=10, pady=10)
        
        self.question_label = ctk.CTkLabel(self.question_frame, text="No questions loaded yet. Please upload a PDF file.")
        self.question_label.pack(fill="x", padx=10, pady=10)
        
        # Create options frame with scrollable area
        self.options_frame_container = ctk.CTkFrame(self.question_frame)
        self.options_frame_container.pack(fill="both", expand=True, padx=10, pady=10)
        
        self.options_canvas = ctk.CTkCanvas(self.options_frame_container, bg="#2b2b2b", highlightthickness=0)
        self.options_canvas.pack(side="left", fill="both", expand=True)
        
        self.options_scrollbar = ctk.CTkScrollbar(self.options_frame_container, orientation="vertical", command=self.options_canvas.yview)
        self.options_scrollbar.pack(side="right", fill="y")
        
        self.options_canvas.configure(yscrollcommand=self.options_scrollbar.set)
        self.options_canvas.bind('<Configure>', lambda e: self.options_canvas.configure(scrollregion=self.options_canvas.bbox("all")))
        
        self.options_frame = ctk.CTkFrame(self.options_canvas)
        self.options_canvas.create_window((0, 0), window=self.options_frame, anchor="nw")
        
        # Create checkboxes (will be populated dynamically)
        self.checkboxes = {}
        self.checkbox_vars = {}
        
        # Create button frame
        self.button_frame = ctk.CTkFrame(self.main_frame)
        self.button_frame.pack(fill="x", padx=10, pady=10)
        
        self.prev_button = ctk.CTkButton(self.button_frame, text="Previous", command=self.prev_question, state="disabled")
        self.prev_button.pack(side="left", padx=10, pady=10)
        
        self.next_button = ctk.CTkButton(self.button_frame, text="Next", command=self.next_question, state="disabled")
        self.next_button.pack(side="left", padx=10, pady=10)
        
        self.check_button = ctk.CTkButton(self.button_frame, text="Check Answer", command=self.check_answer, state="disabled")
        self.check_button.pack(side="right", padx=10, pady=10)
        
        self.show_answer_button = ctk.CTkButton(self.button_frame, text="Show Answer", command=self.show_answer, state="disabled")
        self.show_answer_button.pack(side="right", padx=10, pady=10)
        
        # Create results frame
        self.results_frame = ctk.CTkFrame(self.main_frame)
        self.results_frame.pack(fill="x", padx=10, pady=10)
        
        self.result_label = ctk.CTkLabel(self.results_frame, text="")
        self.result_label.pack(side="left", padx=10, pady=10)
        
        self.score_label = ctk.CTkLabel(self.results_frame, text="Score: 0/0")
        self.score_label.pack(side="right", padx=10, pady=10)
        
    def upload_pdf(self):
        # Open file dialog
        file_path = filedialog.askopenfilename(
            title="Select a PDF file",
            filetypes=[("PDF files", "*.pdf"), ("All files", "*.*")]
        )
        
        if file_path:
            try:
                # Extract questions from the PDF
                self.questions = self.extract_questions_from_pdf(file_path)
                
                if self.questions:
                    self.current_question_index = 0
                    self.user_answers = {}
                    self.score = 0
                    self.score_label.configure(text=f"Score: {self.score}/{len(self.questions)}")
                    self.display_question(self.current_question_index)
                    
                    # Enable buttons
                    self.next_button.configure(state="normal")
                    self.check_button.configure(state="normal")
                    self.show_answer_button.configure(state="normal")
                    
                    if self.current_question_index > 0:
                        self.prev_button.configure(state="normal")
                    else:
                        self.prev_button.configure(state="disabled")
                else:
                    self.question_label.configure(text="No questions found in the PDF file. Please check the format.")
            except Exception as e:
                self.question_label.configure(text=f"Error: {str(e)}")
    
    def extract_questions_from_pdf(self, pdf_path):
        questions = []
        
        try:
            with open(pdf_path, 'rb') as file:
                pdf_reader = PyPDF2.PdfReader(file)
                full_text = ""
                
                # Extract text from all pages
                for page in pdf_reader.pages:
                    full_text += page.extract_text() + "\n"
                
                # Handle line breaks and extra spaces
                full_text = re.sub(r'\s+', ' ', full_text)
                
                # Try multiple regex patterns to match different formats
                # First attempt: Standard format with clear delimiters
                question_blocks = re.split(r'(?=\d+-\s)', full_text)
                
                for block in question_blocks:
                    if not block.strip():
                        continue
                    
                    # Extract question number
                    number_match = re.match(r'(\d+)-\s', block)
                    if not number_match:
                        continue
                    
                    question_number = number_match.group(1)
                    
                    # Check if it's multiple choice
                    is_multiple = "(multiple choice)" in block.lower()
                    
                    # Extract question text
                    question_parts = re.split(r'(?=A\.\s)', block, 1)
                    if len(question_parts) < 2:
                        continue
                    
                    question_text = question_parts[0].replace(f"{question_number}-", "").strip()
                    if is_multiple:
                        question_text = question_text.replace("(multiple choice)", "").strip()
                    
                    # Extract options and correct answer
                    options_text = question_parts[1]
                    options = {}
                    
                    # Extract individual options
                    option_matches = re.findall(r'([A-Z])\.\s+(.*?)(?=[A-Z]\.|Correct Answer:|$)', options_text, re.DOTALL)
                    
                    for option_match in option_matches:
                        option_letter, option_text = option_match
                        options[option_letter] = option_text.strip()
                    
                    # Extract correct answer
                    correct_answer_match = re.search(r'Correct Answer:\s*([A-Z]+)', options_text, re.IGNORECASE)
                    if correct_answer_match:
                        correct_answers = list(correct_answer_match.group(1))
                    else:
                        correct_answers = []
                    
                    # Add question to list if we have options and correct answers
                    if options and correct_answers:
                        questions.append({
                            'number': question_number,
                            'text': question_text,
                            'options': options,
                            'correct_answers': correct_answers,
                            'is_multiple': is_multiple or len(correct_answers) > 1
                        })
                
                # If no questions were found, try an alternative pattern
                if not questions:
                    # Look for questions based on numbering and correct answer markers
                    alt_pattern = r'(\d+)[\.\-]\s*(.*?)\s*([A-Z]\..*?)\s*Correct Answer:\s*([A-Z]+)'
                    alt_matches = re.findall(alt_pattern, full_text, re.DOTALL)
                    
                    for match in alt_matches:
                        question_number, question_text, options_text, correct_answers = match
                        
                        # Check if it's multiple choice
                        is_multiple = "(multiple choice)" in question_text.lower()
                        if is_multiple:
                            question_text = question_text.replace("(multiple choice)", "").strip()
                        
                        # Extract options
                        options = {}
                        option_matches = re.findall(r'([A-Z])\.\s+(.*?)(?=[A-Z]\.|Correct Answer:|$)', options_text, re.DOTALL)
                        
                        for option_match in option_matches:
                            option_letter, option_text = option_match
                            options[option_letter] = option_text.strip()
                        
                        # Add question to list
                        questions.append({
                            'number': question_number,
                            'text': question_text,
                            'options': options,
                            'correct_answers': list(correct_answers),
                            'is_multiple': is_multiple or len(correct_answers) > 1
                        })
            
            # Final check for extracted questions
            if not questions:
                print("Warning: Could not extract questions from the PDF. Please check the format.")
                
        except Exception as e:
            print(f"Error extracting questions: {str(e)}")
            raise e
        
        return questions
    
    def display_question(self, index):
        if not self.questions or index < 0 or index >= len(self.questions):
            return
        
        question = self.questions[index]
        
        # Update question text
        question_text = f"Question {question['number']}: {question['text']}" + (" (multiple choice)" if question['is_multiple'] else "")
        self.question_label.configure(
            text=wrap_text(question_text, width=80)
        )
        
        # Clear previous options
        for widget in self.options_frame.winfo_children():
            widget.destroy()
        
        self.checkboxes = {}
        self.checkbox_vars = {}
        
        # Create new option checkboxes
        for option_letter, option_text in question['options'].items():
            option_display = wrap_text(f"{option_letter}. {option_text}", width=70)
            checkbox = ctk.CTkCheckBox(
                self.options_frame,
                text=option_display
            )
            checkbox.pack(anchor="w", padx=20, pady=5)
            self.checkboxes[option_letter] = checkbox
            self.checkbox_vars[option_letter] = checkbox
        
        # Set checkboxes to user's previous answers if any
        if index in self.user_answers:
            for option_letter, is_selected in self.user_answers[index].items():
                if is_selected:
                    self.checkbox_vars[option_letter].select()
                else:
                    self.checkbox_vars[option_letter].deselect()
        
        # Clear result label
        self.result_label.configure(text="")
        
        # Update buttons
        if index > 0:
            self.prev_button.configure(state="normal")
        else:
            self.prev_button.configure(state="disabled")
        
        if index < len(self.questions) - 1:
            self.next_button.configure(state="normal")
        else:
            self.next_button.configure(state="disabled")
        
        # Reset canvas scroll
        self.options_canvas.yview_moveto(0)
    
    def next_question(self):
        # Save current answers
        self.save_current_answers()
        
        # Move to next question
        if self.current_question_index < len(self.questions) - 1:
            self.current_question_index += 1
            self.display_question(self.current_question_index)
    
    def prev_question(self):
        # Save current answers
        self.save_current_answers()
        
        # Move to previous question
        if self.current_question_index > 0:
            self.current_question_index -= 1
            self.display_question(self.current_question_index)
    
    def save_current_answers(self):
        if not self.questions:
            return
        
        # Get current answers
        current_answers = {}
        for option_letter, checkbox in self.checkbox_vars.items():
            current_answers[option_letter] = checkbox.get()
        
        # Save answers
        self.user_answers[self.current_question_index] = current_answers
    
    def check_answer(self):
        if not self.questions:
            return
        
        # Save current answers
        self.save_current_answers()
        
        # Get current question
        question = self.questions[self.current_question_index]
        
        # Get selected answers
        selected_answers = []
        for option_letter, is_selected in self.user_answers[self.current_question_index].items():
            if is_selected:
                selected_answers.append(option_letter)
        
        # Compare with correct answers
        correct_answers = question['correct_answers']
        is_correct = set(selected_answers) == set(correct_answers)
        
        # Update result label
        if is_correct:
            self.result_label.configure(text="Correct! ✓", text_color="green")
            
            # Update score if this question wasn't already answered correctly
            question_key = f"q_{self.current_question_index}"
            if question_key not in self.user_answers.get('correct_questions', set()):
                self.score += 1
                if 'correct_questions' not in self.user_answers:
                    self.user_answers['correct_questions'] = set()
                self.user_answers['correct_questions'].add(question_key)
        else:
            self.result_label.configure(text="Incorrect ✗", text_color="red")
        
        # Update score label
        self.score_label.configure(text=f"Score: {self.score}/{len(self.questions)}")
        
        # Visual feedback
        for option_letter, checkbox in self.checkboxes.items():
            is_selected = self.user_answers[self.current_question_index][option_letter]
            is_correct_option = option_letter in correct_answers
            
            if is_selected:
                if is_correct_option:
                    checkbox.configure(text_color="green")
                else:
                    checkbox.configure(text_color="red")
            else:
                if is_correct_option:
                    # Highlight missed correct answers
                    checkbox.configure(text_color="orange")
                else:
                    checkbox.configure(text_color=("gray10", "gray90"))  # Default color based on theme
    
    def show_answer(self):
        if not self.questions:
            return
        
        # Get current question
        question = self.questions[self.current_question_index]
        
        # Show correct answers
        correct_letters = ", ".join(question['correct_answers'])
        self.result_label.configure(
            text=f"Correct answer: {correct_letters}",
            text_color="blue"
        )
        
        # Highlight correct options
        for option_letter, checkbox in self.checkboxes.items():
            if option_letter in question['correct_answers']:
                checkbox.configure(text_color="green")
            else:
                checkbox.configure(text_color=("gray10", "gray90"))  # Default color based on theme

if __name__ == "__main__":
    root = ctk.CTk()
    app = QuizApp(root)
    root.mainloop()