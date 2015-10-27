import mako.runtime
import mako.template

pages_revisions_template = '''
<root>
    % for page in pages:
    <page>
        <title>${page.title}</title>
        <ns>${page.namespace}</ns>
        <id>${page.id}</id>
        <revisions>
            % for revision in page.revisions:
            <revision>
                <id>${revision.id}</id>
                <timestamp>${revision.timestamp}</timestamp>
                <references_diff>
                    %for reference_diff in revision.references_diff:
                    <reference_diff action="${reference_diff.action}">${reference_diff.text}</reference_diff>
                    %endfor
                </references_diff>
                <sections>
                    %for section in revision.sections:
                    <section level="${section.level}">${section.name}</section>
                    %endfor
                </sections>
                <bibliography>${revision.bibliography}</bibliography>
            </revision>
            %endfor
        </revisions>
    </page>
    % endfor
</root>
'''

stats_template = '''
<stats>
    <identifiers>
    % for identifier, counts in stats['identifiers'].items():
        <identifier type="${identifier.type}" id="${identifier.id}">
            % for where, count in counts.items():
            <appearance where="${where}" count="${count}" />
            % endfor
        </identifier>
    % endfor
    </identifiers>
</stats>
'''

_default_filters = [
    'str',   # Unicode
    'x',     # XML
]


def _render_xml_template(template, output_handler, **kwargs):
    ctx = mako.runtime.Context(output_handler, **kwargs)

    xml_template = mako.template.Template(
        template,
        default_filters=_default_filters,
    )
    xml_template.render_context(ctx)


def serialize_page_revisions(pages, output_handler):
    _render_xml_template(pages_revisions_template, output_handler, pages=pages)


def serialize_stats(stats, output_handler):
    _render_xml_template(stats_template, output_handler, stats=stats)
