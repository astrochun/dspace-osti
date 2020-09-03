import json
import os

import pandas as pd

class Poster:
    """Use the form input and DSpace metadata to generate the JSON necessary
     for OSTI ingestion. Then post to OSTI using their API"""
    def __init__(self, data_dir='data', to_upload='dataset_metadata_to_upload.json',
     form_input_full_path='form_input.csv', osti_upload='osti.json'):
        self.form_input = form_input_full_path

        self.data_dir = data_dir
        self.to_upload = os.path.join(data_dir, to_upload)
        self.osti_upload = os.path.join(data_dir, osti_upload)

        assert os.path.exists(data_dir)

    def generate_upload_json(self):
        """Validate the form input provided by the user and combine new data
         with DSpace data to generate JSON that is prepared for OSTI ingestion"""

        with open(self.to_upload) as f:
            to_upload_j = json.load(f)

        df = pd.read_csv(self.form_input)
        df = df.set_index('DSpace ID')


        # Validate Input CSV 
        def no_empty_cells(series):
            return series.shape[0] == series.dropna().shape[0]
        def unique_values(series):
            return series.shape[0] == series.unique().shape[0]

        expected_columns = ['Sponsoring Organizations', 'DOE Contract', 'Datatype']
        assert all([col in df.columns for col in expected_columns])
        assert no_empty_cells(df['Sponsoring Organizations'])
        assert no_empty_cells(df['DOE Contract'])
        assert no_empty_cells(df['Datatype'])
        assert no_empty_cells(df['Author'])

        accepted_datatype_values = ['AS','GD', 'IM', 'ND', 'IP', 'FP', 'SM', 'MM', 'I']
        assert all([dt in accepted_datatype_values for dt in df['Datatype']])


        # Generate final JSON to post to OSTI
        osti_format = []
        for dspace_id, row in df.iterrows():
            dspace_data = [item for item in to_upload_j if item['id'] == dspace_id]
            assert len(dspace_data) == 1
            dspace_data = dspace_data[0]
            
            item_dict = {
                'title': dspace_data['name'],
                'creators': ';'.join([m['value'] for m in dspace_data['metadata'] if m['key'] == 'dc.contributor.author']),
                'dataset_type': row['Datatype'],
                'site_url': "https://dataspace.princeton.edu/handle" + dspace_data['handle'],
                'contract_nos': row['DOE Contract'],
                'sponsor_org': row['Sponsoring Organizations'],
                'research_org': 'PPPL',
                'accession_num': dspace_data['handle']
            }

            abstract = [m['value'] for m in dspace_data['metadata'] if m['key'] == 'dc.description.abstract']
            if len(abstract) != 0:
                item_dict['description'] = '\n\n'.join(abstract)

            keywords = [m['value'] for m in dspace_data['metadata'] if m['key'] == 'dc.subject']
            if len(keywords) != 0:
                item_dict['keywords'] = ';'.join(keywords)

            osti_format.append(item_dict)

        with open(self.osti_upload, 'w') as f:
            json.dump(osti_format, f, indent=4)


    def run_pipeline(self):
        self.generate_upload_json()


if __name__ == '__main__':
    p = Poster()
    p.run_pipeline()
