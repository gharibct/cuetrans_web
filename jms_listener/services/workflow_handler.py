import json
import logging
import re
from core.process_types import ProcessType
from core.variable_mapping import variable_mapping
from utils.db.pool_manager import PoolManager
from utils.db.query_loader import sql

logger = logging.getLogger(__name__) 
pool_mgr = PoolManager()

BIND_PLACEHOLDER_RE = re.compile(r":([A-Za-z_][A-Za-z0-9_$#]*)")
LEGACY_PLACEHOLDER_RE = re.compile(r"#([A-Za-z_][A-Za-z0-9_$#]*)#")
QUOTED_LEGACY_PLACEHOLDER_RE = re.compile(r"'#([A-Za-z_][A-Za-z0-9_$#]*)#'")
ERROR_MESSAGE_QUERY = "select error_msg from jms_errormsg where id='#errorId#'"


def preprocess_query(query: str, params: dict | None = None) -> str:
    """Convert legacy #param# placeholders to Oracle named binds."""
    params = params or {}

    def replace_quoted_placeholder(match):
        param_name = match.group(1)
        if param_name not in params:
            return "''"
        return f":{param_name}"

    def replace_placeholder(match):
        param_name = match.group(1)
        if param_name not in params:
            return "''"
        return f":{param_name}"

    query = QUOTED_LEGACY_PLACEHOLDER_RE.sub(replace_quoted_placeholder, query or "")
    return LEGACY_PLACEHOLDER_RE.sub(replace_placeholder, query)


def get_bind_params(query: str, params: dict) -> dict:
    """Return params for every named bind placeholder in the SQL text."""
    bind_names = set(BIND_PLACEHOLDER_RE.findall(query or ""))
    print(bind_names)
    return {key: params[key] for key in bind_names if key in params}
    

def get_column_name(column) -> str:
    return getattr(column, "name", column[0])


def get_row_value(row: dict, key: str, default=None):
    if key in row:
        return row[key]

    key_upper = key.upper()
    for row_key, value in row.items():
        if row_key.upper() == key_upper:
            return value

    return default


def get_validation_status(query_result: dict) -> int:
    if not query_result["rows"]:
        return 1

    return get_row_value(query_result["rows"][0], "validationStatus", 1)

def replace_message_placeholders(message: str, params: dict) -> str:
    def replace(match):
        param_name = match.group(1)
        return str(params.get(param_name, match.group(0)))

    return LEGACY_PLACEHOLDER_RE.sub(replace, message or "")


def get_process_type(process_type: str) -> ProcessType:
    try:
        return ProcessType(process_type)
    except ValueError as exc:
        raise ValueError(f"Unsupported process type: {process_type}") from exc


async def fetch_rows_as_dicts(cursor) -> list[dict]:
    columns = [get_column_name(column) for column in cursor.description]
    rows = await cursor.fetchall()
    return [dict(zip(columns, row)) for row in rows]


async def execute_query(cursor, query: str, params: dict):
    query = preprocess_query(query, params)
    bind_params = get_bind_params(query, params)
    print("bind_params", bind_params,query)
    if bind_params:
        await cursor.execute(query, bind_params)
    else:
        await cursor.execute(query)

    if cursor.description is not None:
        return {
            "rows": await fetch_rows_as_dicts(cursor),
            "rowcount": None
        }
    
    return {
        "rows": [],
        "rowcount": cursor.rowcount
    }


async def fetch_error_message(cursor, error_id: str, params: dict) -> str | None:
    if not error_id or error_id == "x":
        return "Error occurred but no error ID provided"

    query_result = await execute_query(
        cursor,
        ERROR_MESSAGE_QUERY,
        {"errorId": error_id}
    )

    if not query_result["rows"]:
        return "Error message not found"

    error_message = get_row_value(query_result["rows"][0], "ERROR_MSG")
    return replace_message_placeholders(error_message, params)

# ============== Workflow Handler ==============
async def handle_workflow(workFlowName: str, workFlowParams: str):
    """
    Handle workflow request - implement your business logic here
    """
    # Decode the JSON params (same as Ext.JSON.decode)
    try:
        pool = await pool_mgr.get_oracle_pool()
        params = json.loads(workFlowParams)

        # In Python True comes as 1 but in java it comes as true. Hence, if any value is True, then it should be converted to 1
        for key, value in params.items():
            if isinstance(value, bool):
                params[key] = str(value).lower()


        # if strContext is not present in params, then it should be added as null so that sql can handle this as nvl
        if "strContext" not in params:
            params.update({"strContext": ""})

        # This is handcoded intially. This should be removed when login is implemented using JWT
        params.update({"strUserId": "cuetransadmin"})
        params.update({"strOrgId": "cuetrans"})
        params.update({"strLangId": 1})
        params.update({"strRoleId": "admin"})
        params.update({"strTenantId": 1})
        params.update({"strDeptId": 1})        

        result = {
            "hdrcache": [],
            "grid_array": [],
            "combo_array": [],
            "successMsg_array": []
        }

        # geting the query from yaml file
        core_query = sql.get(workFlowName)
        core_query = preprocess_query(core_query, params)

        if not core_query.strip().upper().startswith("SELECT"):
            result["strFailureMsg"] = f"Core query for workflow '{workFlowName}' must be a SELECT statement."
            return result

        errorFlag = False

        async with pool.acquire() as conn:
            conn.autocommit = False  # Ensure we control transactions manually
            try:
                with conn.cursor() as cursor:

                    # MethodName which is required for execution, is alreadly present in the params
                    repository_result = await execute_query(cursor, core_query, params)

                    repository_queries = repository_result["rows"]
                    print(params)
                    for repository_query in repository_queries:

                        if errorFlag:
                            break
                        service_query = repository_query.get("SERVICEQUERY")
                        process_type = repository_query.get("PROCESSTYPE")
                        query_type = repository_query.get("QUERYTYPE")
                        combo_name = repository_query.get("COMBONAME")
                        error_id = repository_query.get("ERRORID")
                        success_id = repository_query.get("SUCCESSID")
                        # if seqno is available in the repository query, then it should be used
                        if repository_query.get("SEQNO") is not None:
                            seq_no = repository_query.get("SEQNO")
                        else:
                            seq_no = 0

                        print(seq_no,process_type, query_type, combo_name, error_id, success_id)
                        await execute_query(cursor, " insert into a values(:seq_no)", {"seq_no": seq_no})

                        if not service_query or service_query.strip() == "" or service_query.strip().upper() == "X":
                            continue

                        # Success Message repository query can be ALL or "". hence, this query should nott be executed
                        # If the query type is init and the error id is not blank, then success message should be fetched
                        if query_type == "Init" and success_id != "" and success_id != "x":
                            success_message = await fetch_error_message(cursor, success_id, params)
                            if success_message:
                                result["strSuccessMsg"] = success_message
                            else:
                                result["strSuccessMsg"] = f"Success message not found for success ID: {success_id}"
                            continue

                        if process_type not in ['HdrProcess', 'HdrFetch',
                                                'ErrorCheck', 'ebPAC', 'ebpac1',
                                                'email', 'UID', 'ebpac'] \
                                                and query_type in ['Validation', 'DML']:
                            # get the combo name and extract the array from params
                            if combo_name == "x":
                                combo_name = process_type
                            combo_array = params.get(combo_name + "_array", [])

                            print(combo_name, combo_array)

                            if not isinstance(combo_array, list):
                                result["strFailureMsg"] = f"Expected a list for combo parameter '{combo_name}', got {type(combo_array).__name__}"
                                errorFlag = True
                                break

                            for combo_params in combo_array:
                                print("combo_params", combo_params)
                                if not isinstance(combo_params, dict):
                                    result["strFailureMsg"] = f"Expected a dict for combo parameters in '{combo_name}', got {type(combo_params).__name__}"
                                    errorFlag = True
                                    break
                                
                                # for each combo params, variable mapping should be called
                                # The return variable should be added without changing combo_params during iteration
                                mapped_combo_params = {}
                                for key, value in combo_params.items():
                                    return_variable = variable_mapping.get_return_variable(core_service=workFlowName, process_type=process_type, key=key)
                                    print(workFlowName,process_type,key)
                                    print("return_variable",return_variable)
                                    if return_variable:
                                        print("Adding ",return_variable)
                                        mapped_combo_params[return_variable] = value

                                # combo params should be merged with params and passed to the query execution
                                merged_params = {**params, **mapped_combo_params}
                                query_result = await execute_query(cursor, service_query, merged_params)

                                # if the query type is validation then count should be extracted
                                if query_type == 'Validation':
                                    count = get_validation_status(query_result)
                                    print("Validation count:", count)
                                    if count == 0:
                                        result["strFailureMsg"] = await fetch_error_message(cursor, error_id, merged_params)
                                        print("Validation failed", error_id, result["strFailureMsg"])
                                        errorFlag = True
                                        break
                        else:
                            query_result = await execute_query(cursor, service_query, params)
                            if query_type == 'Validation':
                                count = get_validation_status(query_result)
                                print("Validation count:", count)
                                if count == 0:
                                    result["strFailureMsg"] = await fetch_error_message(cursor, error_id, params)
                                    print("Validation failed", error_id, result["strFailureMsg"])
                                    errorFlag = True
                                    break


                        if process_type == "HdrFetch":
                            result["hdrcache"].extend(query_result["rows"])

                        if process_type == "MTLFetch":
                            result["grid_array"].append({combo_name: query_result["rows"]})

                        if process_type == "Init":
                            result["combo_array"].append({combo_name: query_result["rows"]})

                        # Adding Success Message
                        if success_id != "" and success_id != "x":
                            success_message = await fetch_error_message(cursor, success_id, params)
                            if success_message:
                                result["strSuccessMsg"] = success_message
                            else:
                                result["strSuccessMsg"] = f"Success message not found for success ID: {success_id}"

                    # COMMIT or ROLLBACK inside the cursor block
                    print("Execution completed")

                    if errorFlag:
                        print(f"Before rollback autocommit={conn.autocommit}")
                        print("Executing rollback due to error")
                        await conn.rollback()
                        print("Rollback completed")
                    else:
                        await conn.commit()

                return result

            except Exception as e:
                # If ANY statement fails, ROLLBACK the entire transaction
                await conn.rollback()
                result["strFailureMsg"] = f"Transaction failed: {e} {repository_query}"
                return result
            
    except json.JSONDecodeError:
        params = {}
    
    logger.info(f"Processing workflow: {workFlowName} ")
    logger.info(f"Params: {params}")
    
    # TODO: Implement your workflow logic here
    
    # Response matching original format
    return {
        "hdrcache": [
            {
                "hdnAuthToken": "new_token_value"
            }
        ]
    }
