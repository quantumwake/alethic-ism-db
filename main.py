# The Alethic Instruction-Based State Machine (ISM) is a versatile framework designed to 
# efficiently process a broad spectrum of instructions. Initially conceived to prioritize
# animal welfare, it employs language-based instructions in a graph of interconnected
# processing and state transitions, to rigorously evaluate and benchmark AI models
# apropos of their implications for animal well-being. 
# 
# This foundation in ethical evaluation sets the stage for the framework's broader applications,
# including legal, medical, multi-dialogue conversational systems.
# 
# Copyright (C) 2023 Kasra Rasaee, Sankalpa Ghose, Yip Fai Tse (Alethic Research) 
# 
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as
# published by the Free Software Foundation, either version 3 of the
# License, or (at your option) any later version.
# 
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
# 
# You should have received a copy of the GNU Affero General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.
# 
# 
from core.processor_state import State
from alethic_ism_db.db.processor_state_db import (
    ProcessorStateDatabaseStorage)

if __name__ == '__main__':
    url = 'postgresql://postgres:postgres1@localhost:5432/postgres'
    db_storage = ProcessorStateDatabaseStorage(database_url=url)

    # animal states load into database
    animal_states = State.load_state('../dataset/animallm/animal_state.json')
    db_storage.save_state(state=animal_states)

    # animal states load into database
    instruction_query_template_states = State.load_state('../dataset/animallm/query_template_state.json')
    db_storage.save_state(state=instruction_query_template_states)

    # animal states load into database
    instruction_query_template_states = State.load_state('../animallm/prod/version0_7/p0_eval/230d7ae5b60054d124a1105b9a76bdf0783efb790c2150a5bcad55a012709295.pickle')
    db_storage.save_state(state=instruction_query_template_states)

    states = db_storage.fetch_states()

    for state in states:
        print(state)
        state_id = state['id']  # fetch state_id
        fetched_state = db_storage.load_state(state_id=state_id)
