import os
import string
import json

def generate_metadata(picklist_name, picklist_value, magento_id):
	metadata_template = string.Template('''<?xml version="1.0" encoding="UTF-8"?>
	<CustomMetadata xmlns="http://soap.sforce.com/2006/04/metadata" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xmlns:xsd="http://www.w3.org/2001/XMLSchema">
		<label>$label</label>
		<protected>false</protected>
		<values>
			<field>Magento_Id__c</field>
			<value xsi:type="xsd:double">$magento_id</value>
		</values>
		<values>
			<field>Pick_List_Mapping__c</field>
			<value xsi:type="xsd:string">$picklist_mapping</value>
		</values>
		<values>
			<field>Salesforce_Value__c</field>
			<value xsi:type="xsd:string">$salesforce_value</value>
		</values>
	</CustomMetadata>''')

	picklist_name_formatted = picklist_name \
		.replace('__c', '')

	picklist_value_formatted = picklist_name_formatted + "_" + picklist_value \
		.replace(" ", "_") \
		.replace("-", "_") \
		.replace("ó", "o") \
		.replace("ö", "o") \
		.replace("ü", "u") \
		.replace("'", "_")

	picklist_value_formatted = picklist_value_formatted[:picklist_value_formatted.index('_ml_(')]

	generated_value = metadata_template.substitute(
		label=f'{picklist_name_formatted}_{picklist_value}'[:40],
		magento_id=magento_id, 
		picklist_mapping=picklist_name_formatted, 
		salesforce_value=picklist_value)

	return (picklist_value_formatted, generated_value)


def main(picklist_name, magento_mapping_file_path, output_directory):
	print(f'Opening magento mapping file {magento_mapping_file_path}')

	# os.path.abspath(os.path.join('CountriesWithRegions', magento_mapping_file_path))

	with open(magento_mapping_file_path, mode='r') as f:
		print('Loading json')

		magento_response = json.load(f)
		
		for item in magento_response:
			(file_name, file_body) = generate_metadata(picklist_name, item['label'], item['value'])
			output_file_name = f'Pick_List_Items_Mapping.{file_name}.md'

			print(f'Writing metadata record for {output_file_name}')

			with open(os.path.join(output_directory, output_file_name), mode='w') as output:
				output.writelines(file_body)
			
		print('Finished generating metadata recods')


if __name__ == '__main__':
	main('Bottle_Content_Size__c', '/Users/roman/Downloads/bottle size.json', os.path.dirname(__file__))