#include <stddef.h> /* for offsetof */
#include "dr_api.h"
#include "drmgr.h"
#include "drreg.h"
#include "drx.h"
#include "droption.h"

//libs
#include <algorithm>
#include <map>
#include <vector>
#include <jansson.h>
#include <ctime>
/// Types
typedef std::map<app_rva_t, uint> BASIC_BLOCKS_INFO_T;
typedef std::map<std::string, BASIC_BLOCKS_INFO_T> MODULE_COVERAGE_INFO_T;

MODULE_COVERAGE_INFO_T modules_coverage;
std::vector<std::string> path_black_list;
std::vector<std::string> path_white_list;
std::vector<std::string> module_black_list;
std::vector<std::string> module_white_list;

droption_t<std::string>  op_file_path(DROPTION_SCOPE_ALL, "file_path","", "Corpus file path","");
droption_t<std::string>  op_config_path(DROPTION_SCOPE_ALL, "config_path", "", "Config file path", "");
droption_t<std::string>  op_out_dir(DROPTION_SCOPE_ALL, "out_dir", "", "Path to store coverage data", "");
droption_t<unsigned int> op_time_out(DROPTION_SCOPE_ALL,"time_out", 99999999, "Timeout in ms","");

void* mutex;

std::string to_lower(const char* str)
{
	std::string data(str);
	std::transform(data.begin(), data.end(), data.begin(), ::tolower);
	return data;
}

const char* get_module_name(const module_data_t* module)
{
	const char *module_name = module->names.exe_name;
	if (module_name == NULL) {
		// In case exe_name is not defined, we will fall back on the preferred name.
		module_name = dr_module_preferred_name(module);
	}
	return module_name;
}
std::string get_random_name(int len = 8)
{
	char tab[] = "0123456789abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ";
	size_t tabSize = strlen(tab);
	char *name = new char[len + 1];
	memset(name, 0, len + 1);
	for (int i = 0; i < len; ++i)
	{
		name[i] = tab[dr_get_random_value(tabSize)];
	}
	return std::string(name);
}
VOID save_instrumentation_infos()
{
	/// basic_blocks_info section
	json_t *bbls_list = json_array();
	json_t *bbl_info = json_object();
	json_t *coverage = json_object();
	json_t *module = json_object();

	for (auto it = modules_coverage.begin(); it != modules_coverage.end(); ++it)
	{
		
		bbls_list = json_array();
		for (auto bbl_it = it->second.begin(); bbl_it != it->second.end(); ++bbl_it)
		{
			bbl_info = json_object();
			json_object_set_new(bbl_info, "bb_rva", json_integer(bbl_it->first));
			json_object_set_new(bbl_info, "bb_size", json_integer(bbl_it->second));
			json_array_append_new(bbls_list, bbl_info);
		}
		module = json_object();
		json_object_set_new(module, "bbls", bbls_list);
		json_object_set_new(coverage, it->first.c_str(), module);
	}
	/// building the tree
	json_t *root = json_object();
	json_object_set_new(root, "coverage", coverage);
	json_object_set_new(root, "corpus_file_path", json_string(op_file_path.get_value().c_str()));
	
	std::string file_log_path = op_out_dir.get_value() + "/" + get_random_name() + ".json";
	FILE* f = fopen(file_log_path.c_str(), "w");
	if (f == nullptr)
	{
		dr_fprintf(STDERR, "[-] Problem with coverage file open\n");
		return;
	}
	dr_fprintf(STDERR, "[+] Saving coverage informations to : %s\n", file_log_path.c_str());
	json_dumpf(root, f, JSON_COMPACT | JSON_ENSURE_ASCII);
	fclose(f);
}

/*
	TODO: Add removing bb from cache after first touch
*/
static dr_emit_flags_t
event_basic_block_analysis(void *drcontext, void *tag, instrlist_t *bb, bool for_trace, bool translating, OUT void **user_data)
{
	instr_t *instr;
	size_t len;
	app_pc start_pc, end_pc, pc;
	module_data_t* module;
	const char* name = "";
		
	/* do nothing for translation */
	if (translating)
		return DR_EMIT_DEFAULT;

	start_pc = dr_fragment_app_pc(tag);
	end_pc = start_pc; /* for finding the size */
	for (instr = instrlist_first_app(bb); instr != NULL; instr = instr_get_next_app(instr)) {
		pc = instr_get_app_pc(instr);
		len = instr_length(drcontext, instr);
		if (pc + len > end_pc)
			end_pc = pc + len;
	}

	module = dr_lookup_module(start_pc);	
	if (!module) 
		return DR_EMIT_DEFAULT;

	name = get_module_name(module);

	app_rva_t bb_rva = start_pc - module->start;
	uint bb_size	 = end_pc - start_pc;

	dr_mutex_lock(mutex);
		modules_coverage[name][bb_rva] = bb_size;
	dr_mutex_unlock(mutex);

	if (module)
		dr_free_module_data(module);

	return DR_EMIT_DEFAULT;
}

bool is_on_black_list(const module_data_t* module)
{
	std::string module_name      = to_lower(get_module_name(module));
	std::string module_full_path = to_lower(module->full_path);
	for each (auto path in path_black_list)
	{		
		if (module_full_path.find(path) != std::string::npos)
			return true;
	}
	for each (auto name in module_black_list)
	{
		if (name == module_name)
			return true;		
	}
	return false;
}
bool is_on_white_list(const module_data_t* module)
{
	std::string module_name = to_lower(get_module_name(module));
	std::string module_full_path = to_lower(module->full_path);
	for each (auto path in path_white_list)
	{
		if (module_full_path.find(path) != std::string::npos)
			return true;
	}
	for each (auto name in module_white_list)
	{
		if (name == module_name)
			return true;
	}
	return false;
}
static void
event_module_load(void *drcontext, const module_data_t *module, bool loaded)
{	
	if (is_on_black_list(module))
	{
		const char* module_name = get_module_name(module);
		dr_fprintf(STDERR, "[+] [BLACKLISTED] Module name : %s\n", module_name);
		dr_module_set_should_instrument(module->handle,false);
		return;
	}
	//if both white list are empty...means let evertyhing beside these modules on black lists
	if (path_white_list.empty() && module_white_list.empty())
		return;
	//check if on white list. in other case treat it as entry on black list
	if (!is_on_white_list(module))
	{
		const char* module_name = get_module_name(module);
		dr_fprintf(STDERR, "[+] [NOT_WHITELISTED] Module name : %s\n", module_name);
		dr_module_set_should_instrument(module->handle, false);
	}
}
BOOL saved = false;
static void
event_exit(void)
{
	dr_fprintf(STDERR, "[+] Exiting\n");
	save_instrumentation_infos();
	dr_mutex_destroy(mutex);
	drreg_exit();
	drmgr_exit();	

}
static void
kill_thread(void*)
{
	dr_sleep(op_time_out.get_value());
	dr_fprintf(STDERR,"[+] Killer thread activated...its time to die\n");
	dr_exit_process(0);
}
static void
load_config()
{	
	//XXX: add reading out_dir,time_out from config file
	if (op_config_path.get_value().empty())
		return;
	dr_fprintf(STDERR, "[+] Time to load config\n");
	json_t *root;
	json_t *property;
	json_t *value;
	std::string string_value;
	json_error_t error;
	std::vector<std::string> config_properties{ "path_black_list", "path_white_list", "module_black_list", "module_white_list"};
	root = json_load_file(op_config_path.get_value().c_str(),0,&error);
	if (!root || !json_is_object(root))
	{
		dr_fprintf(STDERR, "[-] Config error : %s\n", error.text);
		return;
	}
	for each (auto property_name in config_properties)
	{
		property = json_object_get(root, property_name.c_str());
		if (property && json_is_array(property))
		{
			for (int i = 0; i < json_array_size(property); i++)
			{
				value = json_array_get(property, i);
				if (!json_is_string(value)) continue;
				string_value = to_lower(json_string_value(value));
				dr_fprintf(STDERR, "[+] Config value : %s\n", string_value.c_str());
				if (property_name == "path_black_list") path_black_list.push_back(string_value);
				if (property_name == "path_white_list") path_white_list.push_back(string_value);
				if (property_name == "module_black_list") module_black_list.push_back(string_value);
				if (property_name == "module_white_list") module_white_list.push_back(string_value);
			}
		}		
	}
	json_decref(root);
}

static void 
parse_args(int argc, const char *argv[])
{
	std::string parse_err;
	if (!droption_parser_t::parse_argv(DROPTION_SCOPE_CLIENT, argc, argv,&parse_err, NULL)) {
		dr_fprintf(STDERR, "[-] Usage error: %s\nUsage:\n%s", parse_err.c_str(),droption_parser_t::usage_short(DROPTION_SCOPE_ALL).c_str());
		dr_abort();
	}
	if (op_file_path.get_value().empty() || op_out_dir.get_value().empty())
	{
		dr_fprintf(STDERR, "[-] Usage error: file_path and out_dir is required\nUsage:\n%s",	droption_parser_t::usage_short(DROPTION_SCOPE_ALL).c_str());
		dr_abort();
	}	
	load_config();
}

DR_EXPORT void
dr_client_main(client_id_t id, int argc, const char *argv[])
{
	drreg_options_t ops = { sizeof(ops), 1 /*max slots needed: aflags*/, false };
	dr_set_client_name("VizCov by Icewall'","http://github.com/icewall/vizcov");

	if (!drmgr_init() || drreg_init(&ops) != DRREG_SUCCESS || !drx_init())
		DR_ASSERT(false);	

	/* parse arguments */
	parse_args(argc, argv);

	/* register events */
	dr_register_exit_event(event_exit);
	drmgr_register_module_load_event(event_module_load);
	drmgr_register_bb_instrumentation_event(event_basic_block_analysis, NULL, NULL);

	/* start our random-generator machine */
	dr_set_random_seed(clock()+dr_get_process_id());

	/* Kill process after specified timeout */
	dr_create_client_thread(kill_thread,0);

	/* create mutex */
	mutex = dr_mutex_create();

	/* make it easy to tell, by looking at log file, which client executed */
	dr_log(NULL, LOG_ALL, 1, "VizCov client is running\n");
	if (dr_is_notify_on()) {
		/* ask for best-effort printing to cmd window.  must be called at init. */
		dr_enable_console_printing();
		dr_fprintf(STDERR, "VizCov client is running\n");
	}	
}
