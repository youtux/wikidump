import mako.runtime
import mako.template


xml_template_str = '''
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
    <stats>
        <identifiers>
        % for identifier, counts in stats['identifiers'].items():
            <identifier type="${identifier.type}" id="${identifier.id}">
                % for where, count in counts.items():
                <appearance where="${where}" count="${count}" />
                % endfor
        % endfor
        </identifiers>
    </stats>
</root>
'''


def serialize(pages, stats, output_handler):
    xml_template = mako.template.Template(xml_template_str)
    ctx = mako.runtime.Context(output_handler, pages=pages, stats=stats)

    xml_template.render_context(ctx)
