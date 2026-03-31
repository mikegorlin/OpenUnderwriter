"""Section renderers for the D&O underwriting worksheet.

Each section module renders one major section of the worksheet
into a python-docx Document. Sections 1-4 in Plan 02, 5-7 in Plan 03.
Meeting prep appendix in Plan 04.
"""

from do_uw.stages.render.sections.meeting_prep import render_meeting_prep
from do_uw.stages.render.sections.sect1_executive import render_section_1
from do_uw.stages.render.sections.sect2_company import render_section_2
from do_uw.stages.render.sections.sect3_financial import render_section_3
from do_uw.stages.render.sections.sect4_market import render_section_4
from do_uw.stages.render.sections.sect5_governance import render_section_5
from do_uw.stages.render.sections.sect6_litigation import render_section_6
from do_uw.stages.render.sections.sect6_timeline import render_litigation_details
from do_uw.stages.render.sections.sect7_coverage_gaps import render_coverage_gaps
from do_uw.stages.render.sections.sect7_peril_map import render_peril_map
from do_uw.stages.render.sections.sect7_scoring import render_section_7

__all__ = [
    "render_coverage_gaps",
    "render_litigation_details",
    "render_meeting_prep",
    "render_peril_map",
    "render_section_1",
    "render_section_2",
    "render_section_3",
    "render_section_4",
    "render_section_5",
    "render_section_6",
    "render_section_7",
]
