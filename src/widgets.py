import io
import os
import json
from functools import lru_cache
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Union

# from ipyevents import Event
from ipywidgets import widgets

BASE_PATH = Path(os.getenv('CLINEX_BASE_PATH', '.'))
CONTENT_COLOR = (0, 255, 0, 64)  # green
EXCLUDED_COLOR = (255, 0, 0, 128)  # red
HIGHLIGHT_COLOR1 = (255, 225, 0, 64)  # yellow
HIGHLIGHT_COLOR2 = (255, 32, 0, 64)  # orange
HIGHLIGHT_COLOR3 = (0, 32, 255, 32)  # blue
FADE_COLOR = (255, 255, 255, 160)  # white


class BaseWidget(widgets.VBox):

    def __init__(self, image_size: int = 1200):

        self.debug_output = widgets.Output(layout=widgets.Layout(margin='20px 0 0 0'))
        self.quiz = widgets.VBox()

        super().__init__((
            self.quiz,
            self.debug_output
        ))

    @property
    def capture_output(self):
        return self.debug_output.capture(clear_output=True)

    def update(self, refresh: bool = False) -> None:
        self.update_callback(False, False)

    def update_callback(self, document_changed: bool, page_changed: bool) -> None:
        pass

class QuizWidget(BaseWidget):

    def __init__(self, n: int = 100, image_size: int = 1200):
        super().__init__(image_size=image_size)

        def validated_checkbox():
            return widgets.Checkbox(description='Validated', indent=False, layout=widgets.Layout(margin='0 0 0 20px', width='80px'))

        def clear_button():
            return widgets.Button(icon='eraser', layout=widgets.Layout(width='35px'))

        def row(label, elements):
            return widgets.VBox((widgets.Label(label), widgets.HBox(elements)), layout=widgets.Layout(margin='20px 0 0 0'))

        def question_row(question, options):
            button = widgets.ToggleButtons(options=[(option, i) for i, option in enumerate(options)])
            return widgets.VBox((widgets.Label(question), button),
                                layout=widgets.Layout(margin='20px 0 0 0'))
        
        def section_area(name, questions):
            return widgets.VBox((widgets.Label(' '.join([word.capitalize() for word in name.split('_')])),
                                 widgets.VBox(questions)),
                                 layout=widgets.Layout(margin='20px 0 0 0',
                                                       border='1px solid #ccc'),
                                                       padding='20px')
                
        self.buttons = []
        
        # Quiz header
        self.title                      = widgets.HTML('<span style="margin-left: 10px; font-size: 32px, font-style: italic; font-weight: bold; color: #888888;"> \
                                                        Fitzpatrick Skin Type Quiz \
                                                        </span>')
        
        self.completion_status_output   = widgets.HTML()
        self.mq_doc_type_output         = widgets.HTML()
        
        self.override_check_buttons = widgets.ToggleButtons(options=[('Yes', True), ('No', False)])
        self.override_check_row     = row('Do you already know your Fitzpatrick Skin Type?', (self.override_check_buttons, self.mq_doc_type_output))
        
        self.skin_type_dropdown     = widgets.Dropdown(options=[('I', 150),('II', 220),('III', 290),('IV', 370),('V', 440),('VI', 440)], layout=widgets.Layout(width='400px'))
        self.skin_type_row          = row('Choose your skin type:', (self.skin_type_dropdown, ))
        
        
        # Quiz content
        src = Path('./src')
        
        with open(src / 'quiz.json', 'r') as read_file:
            quizdata = json.load(read_file)
        
        sections = []
        for section_name, questions in quizdata.items():
            section = []
            for question, options in questions.items():
                qrow = question_row(question, options)
                self.add_button(question, options)
                section.append(qrow)
            sections.append(section_area(section_name, tuple(section)))
            
            
        self.sections = widgets.VBox(tuple(sections), layout=widgets.Layout(margin='20px 0 0 0'))
        
        
        # Quiz footer
        self.note_textarea = widgets.Textarea(layout=widgets.Layout(width='800px'))
        self.note_row = row('Note', (self.note_textarea, ))
        
        self.save_button = widgets.Button(description='Save', icon='save', layout=widgets.Layout(width='120px'))
        self.save_button.style.button_color = '#52BE80'
        self.save_button.on_click(self.capture_output(lambda _: self.save_values()))
        
        self.reset_button = widgets.Button(icon='undo', layout=widgets.Layout(width='35px'))
        self.reset_button.on_click(self.capture_output(lambda _: self.reset_form()))
        
        self.save_row = widgets.HBox((self.save_button, self.reset_button, 
                                      widgets.HTML('<span style="margin-left: 20px; font-style: italic; color: #888888;">Hint: Auto-saves on document change!</span>')), 
                                     layout=widgets.Layout(margin='30px 0 0 0'))

        self.inputs = [
            self.override_check_buttons,
            self.skin_type_dropdown,
            self.note_textarea
        ]

        for c in self.inputs + self.buttons:
            c.observe(self.capture_output(self.handle_value_change), 'value')
            if isinstance(c, widgets.ToggleButtons):
                c.style.button_width = '200px'

        self.values_changed = False

        self.quiz.children = (
            self.title,
            self.override_check_row,
            self.skin_type_row,
            self.sections,
            self.note_row,
            self.save_row,
        )
        
        self.reset_form()
                
        self.quiz.layout.width = '950px'
        self.quiz.layout.margin = '0 0 0 20px'
        self.quiz.layout.border = '1px solid #ccc'
        self.quiz.layout.padding = '20px'
        
    def add_button(self, question, options):
        button = widgets.ToggleButtons(options=[(option, i) for i, option in enumerate(options)])
        self.buttons.append(button)

    def handle_value_change(self, change: Dict[str, Any]) -> None:
        self.values_changed = True
        owner = change['owner']
        self.update_form()

    def initialise_form(self) -> None:
        for r in self.quiz.children:
            if r not in {self.title, self.override_check_row, self.save_row}:
                r.layout.display = 'none'
        
    def reset_form(self) -> None:
        for element in self.inputs + self.buttons:
            if type(element.value) is str:
                element.value = ''
            else:
                element.value = None
        self.initialise_form()
        
    def update_form(self) -> None:
        if self.override_check_buttons.value == True:
            for r in self.quiz.children:
                if r not in {self.title, self.override_check_row,  self.skin_type_row, self.save_row}:
                    r.layout.display = 'none'
                self.skin_type_row.layout.display = None
        elif self.override_check_buttons.value == False:
            for r in self.quiz.children:
                r.layout.display = None
            self.skin_type_row.layout.display = 'none'
                            
        self.update_completion_status()
        
    @property
    def completion_status(self) -> float:
        if self.override_check_buttons.value:
            return 1.0
        else:
            return 0

    def update_completion_status(self):
        def show_completion_status(status, color):
            self.completion_status_output.value = f'<div style="color: {color}; font-weight: bold; font-size: 16px;">{status}</div>'

        if self.completion_status == 1:
            show_completion_status('Completed', 'green')
        elif self.completion_status > 0:
            show_completion_status('Partially validated', 'orange')
        else:
            show_completion_status('Not yet validated', 'red')

    def get_values(self) -> Dict[str, Any]:
        return {
            'eye_colour': self.eye_colour_buttons.value,
            'hair_colour': self.hair_colour_buttons.value,
            'skin_colour': self.skin_colour_buttons.value,
            'freckles': self.freckles_buttons.value,
            'note': self.note_textarea.value
        }
