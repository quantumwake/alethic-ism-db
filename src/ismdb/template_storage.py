import uuid
import logging as log
from typing import Optional, List

from ismcore.model.base_model import InstructionTemplate
from ismcore.storage.processor_state_storage import TemplateStorage

from ismdb.base import BaseDatabaseAccessSinglePool

logging = log.getLogger(__name__)


class TemplateDatabaseStorage(TemplateStorage, BaseDatabaseAccessSinglePool):

    def fetch_templates(self, project_id: str = None) -> Optional[List[InstructionTemplate]]:
        return self.execute_query_many(
            sql="SELECT * FROM template",
            conditions={
                'project_id': project_id
            },
            mapper=lambda row: InstructionTemplate(**row))

    def fetch_template(self, template_id: str) -> InstructionTemplate:
        return self.execute_query_one(
            sql="SELECT * FROM template",
            conditions={
                'template_id': template_id
            },
            mapper=lambda row: InstructionTemplate(**row))

    def delete_template(self, template_id):
        try:
            conn = self.create_connection()
            with conn.cursor() as cursor:
                sql = """DELETE FROM template WHERE template_id = %s"""
                cursor.execute(sql, [template_id])
            conn.commit()
        except Exception as e:
            logging.error(e)
            raise e
        finally:
            self.release_connection(conn)

    def insert_template(self, template: InstructionTemplate = None) -> InstructionTemplate:

        try:
            conn = self.create_connection()
            with conn.cursor() as cursor:
                sql = """
                          MERGE INTO template AS target
                          USING (SELECT 
                                   %s AS template_id, 
                                   %s AS template_path, 
                                   %s AS template_content, 
                                   %s AS template_type,
                                   %s AS project_id) AS source
                             ON target.template_id = source.template_id 
                          WHEN MATCHED THEN 
                              UPDATE SET 
                                template_path = source.template_path,
                                template_type = source.template_type, 
                                template_content = source.template_content
                          WHEN NOT MATCHED THEN 
                              INSERT (template_id, template_path, template_content, template_type, project_id)
                              VALUES (
                                   source.template_id, 
                                   source.template_path, 
                                   source.template_content, 
                                   source.template_type,
                                   source.project_id
                              )
                      """

                # create a template id if it is not specified
                template.template_id = template.template_id if template.template_id else str(uuid.uuid4())

                values = [
                    template.template_id,
                    template.template_path,
                    template.template_content,
                    template.template_type,
                    template.project_id
                ]
                cursor.execute(sql, values)

            conn.commit()
        except Exception as e:
            logging.error(e)
            raise e
        finally:
            self.release_connection(conn)

        return template

