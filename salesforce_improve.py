import logging
import pandas as pd
from simple_salesforce import Salesforce, SalesforceMalformedRequest, SalesforceGeneralError, \
    SalesforceMoreThanOneRecord, SalesforceExpiredSession, SalesforceRefusedRequest, SalesforceResourceNotFound


# OPERATIONS ###############################################################################
class Salesforce_Improve:
    def __init__(self, user, password, security_token, domain=None):
        self.user = user
        self.password = password
        self.security_token = security_token
        self.domain = domain
        if self.domain is None:
            self.sf = Salesforce(username=self.user,
                                 password=self.password,
                                 security_token=self.security_token)
        else:
            self.sf = Salesforce(username=self.user,
                                 password=self.password,
                                 security_token=self.security_token,
                                 domain=self.domain)

    READ = 'read'
    INSERT = 'insert'
    UPSERT = 'upsert'
    UPDATE = 'update'
    DELETE = 'delete'


# OBJECTS ###################################################################################
    ACCOUNTS = 'Account'
    CASES = 'Case'
    LEADS = 'Lead'
    CONTRACTS = 'Contract'
    CONTACTS = 'Contact'
    APPLICATION_LOG = 'ApplicationLog__c'


# FUNCTIONS #################################################################################

    def write_log(self,obj, message, total_records, failed_records):
        json_log = {'Process__c': obj,  # { Tomadores, Apólices }
                    'Message__c': message,
                    'TotalRecords__c': str(total_records),
                    'FailedRecords__c': str(failed_records)}
        self.sf_single_operation(Salesforce_Improve.INSERT, self.APPLICATION_LOG, json_log)
        return 0  # Return a boolean indicating success or failure

    def create_log_upsert(self,object, results):
        errors = ''

        for error in results[results['success'] == False].iterrows():
            errors += error[1]['errors'][0]['message'] + '\n'


        total_records = len(results)
        failed_records = len(results[results['success'] == False])

        log = {'TotalRecords__c': int(total_records),
               'FailedRecords__c': failed_records,
               'Process__c': object,  # { Tomadores, Apólices }
               'Message__c': errors[:1000]
               }

        self.sf_single_operation(Salesforce_Improve.INSERT, self.APPLICATION_LOG, log)
        return 0

    def create_log_api_call(self,object, response):
        # Assuming 'response' is the response object from a requests API call
        success = response.status_code == 200
        message = response.text if not success else ''

        log = {
            'TotalRecords__c': 1 if success else 0,
            'FailedRecords__c': 0 if success else 1,
            'Process__c': object,  # API call type or identifier
            'Message__c': message[:1000]
        }

        self.sf_single_operation(Salesforce_Improve.INSERT, self.APPLICATION_LOG, log)
        return success


    def sf_single_operation(self,operation, object_type, json_in):
        json_out = ''
        r = 0
        try:
            if operation == Salesforce_Improve.INSERT:
                time.sleep(1)
                r = eval(f"self.sf.{object_type}.create({json_in})")

        except SalesforceMoreThanOneRecord as e:
            json_out = {'Status': '400 Bad Request', 'Message': e.content[0]['message']}
        except SalesforceMalformedRequest as e:
            json_out = {'Status': '400 Bad Request', 'Message': e.content[0]['message']}
        except SalesforceExpiredSession as e:
            json_out = {'Status': '400 Bad Request', 'Message': e.content[0]['message']}
        except SalesforceRefusedRequest as e:
            json_out = {'Status': '400 Bad Request', 'Message': e.content[0]['message']}
        except SalesforceResourceNotFound as e:
            json_out = {'Status': '400 Bad Request', 'Message': e.content[0]['message']}
        except SalesforceGeneralError as e:
            json_out = {'Status': '400 Bad Request', 'Message': e.content[0]['message']}
        else:
            if operation == Salesforce_Improve.READ:
                json_out = r['records'][0]
            else:
                if r == 204:
                    json_out = {'Registo Actualizado'}
                else:
                    json_out = {'Registo Inserido'}
        finally:
            return json_out


    def sf_get_id(self,object, field, value):
        query = f"SELECT Id FROM {object} WHERE {field} = {value}"
        records = self.sf.query_all(query)
        if records['totalSize'] == 0:
            return None
        else:
            return records['records'][0]['Id']

    def sf_bulk_operation(self,operation, object_type, input_df=None, fields='Id, Name', where=None, pk=None, limit=None):
        logging.info('(sf_bulk_operation) >>>>>>>> Start')
        logging.info(' '.join(['(sf_bulk_operation)', operation, object_type]))
        records = []
        data = []
        try:
            match operation:
                case Salesforce_Improve.READ:
                    query = f"SELECT {fields} FROM {object_type}"
                    if where:
                        query += f" WHERE {where}"
                    if limit:
                        query += f" LIMIT {limit}"
                    records = eval(f"self.sf.bulk.{object_type}.query('{query}')")

                case Salesforce_Improve.DELETE:
                    input = input_df[['Id']]
                    data = input.to_dict('records')
                    records = eval(f"self.sf.bulk.{object_type}.delete(data, batch_size=5000, use_serial=True)")

                case Salesforce_Improve.INSERT | Salesforce_Improve.UPDATE:
                    data = input_df.to_dict('records')
                    records = eval(f"self.sf.bulk.{object_type}.{operation}(data, batch_size=5000, use_serial=True)")

                case Salesforce_Improve.UPSERT:
                    data = input_df.to_dict('records')
                    if pk:
                        pk = object_type.replace('__c', 'PK__c')
                    records = eval(f"self.sf.bulk.{object_type}.upsert(data, '{pk}', batch_size=5000, use_serial=True)")
                case _:
                    logging.info(' '.join(['(sf_bulk_operation)', 'Invalid operation']))
                    return
        except SalesforceMoreThanOneRecord as e:
            logging.info(' '.join(['(sf_bulk_operation)', e.content[0]['message']]))
        except SalesforceMalformedRequest as e:
            logging.info(' '.join(['(sf_bulk_operation)', e.content[0]['message']]))
        except SalesforceExpiredSession as e:
            logging.info(' '.join(['(sf_bulk_operation)', e.content[0]['message']]))
        except SalesforceRefusedRequest as e:
            logging.info(' '.join(['(sf_bulk_operation)', e.content[0]['message']]))
        except SalesforceResourceNotFound as e:
            logging.info(' '.join(['(sf_bulk_operation)', e.content[0]['message']]))
        except SalesforceGeneralError as e:
            logging.info(' '.join(['(sf_bulk_operation)', e.content[0]['message']]))
        else:
            df = pd.DataFrame()
            if len(records) > 0:
                df = pd.DataFrame(records)
                if operation == Salesforce_Improve.READ:
                    df.drop(columns=['attributes'], inplace=True)
                if operation == Salesforce_Improve.UPSERT:
                    df = pd.merge(input_df, df, left_index=True, right_index=True, how='inner')
                if operation == Salesforce_Improve.DELETE:
                    df = pd.merge(input_df, df, left_index=True, right_index=True, how='inner')
            logging.info('(sf_bulk_operation) >>>>>>>> End')
            return df




