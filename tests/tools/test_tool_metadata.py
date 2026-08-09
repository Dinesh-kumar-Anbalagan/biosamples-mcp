from tools.get_sample_tool_service import GetSampleToolService
from tools.search_samples_tool_service import SearchSamplesToolService
from tools.server_info_tool_service import ServerInfoToolService
from tools.submit_sample_tool_service import SubmitSampleToolService

def test_tool_metadata_names_are_registered():
    assert GetSampleToolService.__is_tool__ is True
    assert GetSampleToolService.__tool_name__ == "biosamples_getsample"
    assert "accession" in GetSampleToolService.__input_schema__["required"]

    assert SearchSamplesToolService.__is_tool__ is True
    assert SearchSamplesToolService.__tool_name__ == "biosamples_searchsamples"
    assert "query" in SearchSamplesToolService.__input_schema__["required"]

    assert SubmitSampleToolService.__is_tool__ is True
    assert SubmitSampleToolService.__tool_name__ == "biosamples_submitsample"
    assert "submissionSample" in SubmitSampleToolService.__input_schema__["required"]

    assert ServerInfoToolService.__is_tool__ is True
    assert ServerInfoToolService.__tool_name__ == "biosamples_serverinfo"