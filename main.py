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
