import collections

from flask import (
    Blueprint, flash, render_template, redirect, request, url_for
)

from webapp.home.metapype_client import (
    add_child, create_project, create_related_project,
    remove_related_project, load_eml, save_both_formats,
    add_paragraph_tags, remove_paragraph_tags,
    list_funding_awards, create_funding_award,
    remove_child, UP_ARROW, DOWN_ARROW,
    get_upval, get_downval
)

from webapp.home.forms import is_dirty_form, form_md5
from webapp.home.views import non_breaking, process_up_button, process_down_button

from webapp.views.project.forms import (
    ProjectForm, AwardSelectForm, AwardForm, RelatedProjectSelectForm
)

from webapp.views.responsible_parties.rp import rp_select_get
from webapp.views.responsible_parties.forms import ResponsiblePartySelectForm

from webapp.buttons import *
from webapp.pages import *
from webapp.home.views import select_post, set_current_page, get_help
from metapype.eml import names
from metapype.model.node import Node


proj_bp = Blueprint('proj', __name__, template_folder='templates')


@proj_bp.route('/project/<filename>', methods=['GET', 'POST'])
@proj_bp.route('/project/<filename>/<node_id>', methods=['GET', 'POST'])
def project(filename=None, node_id=None):
    form = ProjectForm(filename=filename)
    eml_node = load_eml(filename=filename)
    if eml_node:
        dataset_node = eml_node.find_child(names.DATASET)
        if not dataset_node:
            dataset_node = Node(names.DATASET, parent=eml_node)
            add_child(eml_node, dataset_node)

    # Process POST
    if request.method == 'POST' and form.validate_on_submit():
        save = False
        if is_dirty_form(form):
            save = True
        # flash(f'save: {save}')

        if 'Next' in request.form:
            if not node_id:
#PT5/26                new_page = PAGE_OTHER_ENTITY_SELECT
                new_page = PAGE_DONOR  #PT5/26
            else:
                new_page = PAGE_RELATED_PROJECT_SELECT
        elif BTN_PROJECT_PERSONNEL in request.form:
            new_page = PAGE_PROJECT_PERSONNEL_SELECT
        elif BTN_FUNDING_AWARDS in request.form:
            new_page = PAGE_FUNDING_AWARD_SELECT
        elif BTN_RELATED_PROJECTS in request.form:
            new_page = PAGE_RELATED_PROJECT_SELECT
        elif BTN_HIDDEN_CHECK in request.form:
            new_page = PAGE_CHECK
        elif BTN_HIDDEN_SAVE in request.form:
            new_page = PAGE_PROJECT
        elif BTN_HIDDEN_DOWNLOAD in request.form:
            new_page = PAGE_DOWNLOAD
        elif BTN_HIDDEN_NEW in request.form:
            new_page = PAGE_CREATE
        elif BTN_HIDDEN_OPEN in request.form:
            new_page = PAGE_OPEN
        elif BTN_HIDDEN_CLOSE in request.form:
            new_page = PAGE_CLOSE

        if save:
            title = form.title.data
            abstract = add_paragraph_tags(form.abstract.data)
            if not node_id:
                create_project(dataset_node, title, abstract)
            else:
                related_project_node = create_related_project(dataset_node, title, abstract, node_id)
                node_id = related_project_node.id
            save_both_formats(filename=filename, eml_node=eml_node)

        if not node_id:
            return redirect(url_for(new_page, filename=filename))
        else:
            return redirect(url_for(new_page, filename=filename, node_id=node_id))

    # Process GET
    if node_id == '1':
        form.init_md5()
    elif node_id:
        related_project_node = Node.get_node_instance(node_id)
        populate_project_form(form, related_project_node)
    elif dataset_node:
        project_node = dataset_node.find_child(names.PROJECT)
        populate_project_form(form, project_node)

    set_current_page('project')
    if not node_id:
        help = [get_help('project'), get_help('project_title')]
    else:
        help = [get_help('related_project'), get_help('project_title')]
    if not node_id:
        page_title = 'Project'
    else:
        page_title = 'Related Project'
    return render_template('project.html',
                           title=page_title,
                           filename=filename,
                           form=form,
                           help=help)


def populate_project_form(form: ProjectForm, project_node: Node):
    title = ''
    abstract = ''

    if project_node:
        title_node = project_node.find_child(names.TITLE)
        if title_node:
            title = title_node.content

        abstract_node = project_node.find_child(names.ABSTRACT)
        if abstract_node:
            abstract = abstract_node.content
            if not abstract:
                para_node = abstract_node.find_child(names.PARA)
                if para_node:
                    if para_node.content:
                        abstract = para_node.content
                else:
                    section_node = abstract_node.find_child(names.SECTION)
                    if section_node:
                        abstract = section_node.content
            abstract = abstract

        form.title.data = title
        form.abstract.data = remove_paragraph_tags(abstract)
    form.md5.data = form_md5(form)


@proj_bp.route('/project_personnel_select/<filename>', methods=['GET', 'POST'])
@proj_bp.route('/project_personnel_select/<filename>/<node_id>', methods=['GET', 'POST'])
def project_personnel_select(filename=None, node_id=None):
    form = ResponsiblePartySelectForm(filename=filename)

    # Process POST
    if request.method == 'POST':
        form_value = request.form
        form_dict = form_value.to_dict(flat=False)
        url = select_post(filename, form, form_dict,
                          'POST', PAGE_PROJECT_PERSONNEL_SELECT, PAGE_PROJECT,
                          PAGE_PROJECT, PAGE_PROJECT_PERSONNEL, project_node_id=node_id)
        return redirect(url)

    # Process GET
    help = [get_help('project_personnel')]
    return rp_select_get(filename=filename, form=form, rp_name='personnel',
                         rp_singular=non_breaking('Project Personnel'), rp_plural=non_breaking('Project Personnel'),
                         node_id=node_id, help=help)


@proj_bp.route('/funding_award_select/<filename>', methods=['GET', 'POST'])
@proj_bp.route('/funding_award_select/<filename>/<node_id>', methods=['GET', 'POST'])
def funding_award_select(filename=None, node_id=None):
    form = AwardSelectForm(filename=filename)

    # Process POST
    if request.method == 'POST':
        form_value = request.form
        form_dict = form_value.to_dict(flat=False)
        project_node_id = None

        if form_dict:
            for key in form_dict:
                val = form_dict[key][0]  # value is the first list element
                if val == BTN_SAVE_AND_CONTINUE:
                    new_page = PAGE_PROJECT
                elif val[0:4] == 'Back':
                    new_page = PAGE_PROJECT
                    project_node_id = node_id
                elif val == BTN_EDIT:
                    new_page = PAGE_FUNDING_AWARD
                    project_node_id = node_id
                    node_id = key
                elif val == BTN_REMOVE:
                    new_page = PAGE_FUNDING_AWARD_SELECT
                    project_node_id = node_id
                    node_id = key
                    eml_node = load_eml(filename=filename)
                    remove_child(node_id=node_id)
                    save_both_formats(filename=filename, eml_node=eml_node)
                elif val == BTN_HIDDEN_CHECK:
                    new_page = PAGE_CHECK
                elif val == BTN_HIDDEN_SAVE:
                    new_page = PAGE_FUNDING_AWARD_SELECT
                elif val == BTN_HIDDEN_DOWNLOAD:
                    new_page = PAGE_DOWNLOAD
                elif val == BTN_HIDDEN_NEW:
                    new_page = PAGE_CREATE
                elif val == BTN_HIDDEN_OPEN:
                    new_page = PAGE_OPEN
                elif val == BTN_HIDDEN_CLOSE:
                    new_page = PAGE_CLOSE
                elif val == UP_ARROW:
                    new_page = PAGE_FUNDING_AWARD_SELECT
                    node_id = key
                    process_up_button(filename, node_id)
                elif val == DOWN_ARROW:
                    new_page = PAGE_FUNDING_AWARD_SELECT
                    node_id = key
                    process_down_button(filename, node_id)
                elif val[0:3] == 'Add':
                    new_page = PAGE_FUNDING_AWARD
                    project_node_id = node_id
                    node_id = '1'

        if form.validate_on_submit():
            if node_id and project_node_id:
                url = url_for(new_page,
                              filename=filename,
                              node_id=node_id,
                              project_node_id=project_node_id)
            elif node_id:
                url = url_for(new_page,
                              filename=filename,
                              node_id=node_id)
            else:
                url = url_for(new_page,
                              filename=filename)
            return redirect(url)

    # Process GET
    return funding_award_select_get(filename=filename, form=form, node_id=node_id)


def funding_award_select_get(filename=None, form=None, node_id=None):
    # Process GET
    title = 'Funding Awards'
    # entity_name = ''
    eml_node = load_eml(filename=filename)

    funding_award_list = list_funding_awards(eml_node, node_id)
    set_current_page('project')
    related_project = node_id is not None
    help = [get_help('awards')]
    return render_template('award_select.html', title=title,
                           filename=filename,
                           award_list=funding_award_list,
                           form=form, help=help, related_project=related_project)


@proj_bp.route('/funding_award/<filename>/<node_id>', methods=['GET', 'POST'])
@proj_bp.route('/funding_award/<filename>/<node_id>/<project_node_id>', methods=['GET', 'POST'])
def funding_award(filename=None, node_id=None, project_node_id=None):
    form = AwardForm(filename=filename)

    eml_node = load_eml(filename=filename)
    if not project_node_id:
        project_node = eml_node.find_single_node_by_path([
            names.DATASET,
            names.PROJECT
        ])
    else:
        project_node = Node.get_node_instance(project_node_id)
    if request.method == 'POST':
        form_value = request.form
        form_dict = form_value.to_dict(flat=False)

        if request.method == 'POST' and BTN_CANCEL in request.form:
            url = url_for(PAGE_FUNDING_AWARD_SELECT, filename=filename, node_id=project_node_id)
            return redirect(url)

        # if request.method == 'POST' and form.validate_on_submit():
        if request.method == 'POST':
            next_page = PAGE_FUNDING_AWARD_SELECT

        submit_type = None
        if is_dirty_form(form):
            submit_type = 'Save Changes'
        # flash(f'submit_type: {submit_type}')

        if submit_type == 'Save Changes':
            funder_name = form.funder_name.data
            award_title = form.award_title.data
            funder_identifier = form.funder_identifier.data
            award_number = form.award_number.data
            award_url = form.award_url.data

            award_node = Node(names.AWARD, parent=project_node)

            create_funding_award(award_node, funder_name, award_title, funder_identifier, award_number, award_url)

            if node_id and len(node_id) != 1:
                old_award_node = Node.get_node_instance(node_id)

                if old_award_node:
                    award_parent_node = old_award_node.parent
                    award_parent_node.replace_child(old_award_node, award_node)
                else:
                    msg = f"No funding award node found in the node store with node id {node_id}"
                    raise Exception(msg)
            else:
                add_child(project_node, award_node)

            save_both_formats(filename=filename, eml_node=eml_node)

        url = select_post(filename, form, form_dict,
                          'POST', PAGE_FUNDING_AWARD_SELECT, PAGE_PROJECT,
                          PAGE_FUNDING_AWARD_SELECT, PAGE_FUNDING_AWARD, project_node_id=project_node_id)
        return redirect(url)

    # Process GET
    if not project_node_id:
        title = 'Project Funding Award'
        related_project = False
    else:
        title = 'Related Project Funding Award'
        related_project = True

    if node_id == '1':
        form.init_md5()
    else:
        award_nodes = project_node.find_all_children(names.AWARD)
        if award_nodes:
            for award_node in award_nodes:
                if node_id == award_node.id:
                    populate_award_form(form, award_node)
                    break

    set_current_page('project')
    help = [get_help('award'),
            get_help('funder_name'),
            get_help('award_title'),
            get_help('funder_identifiers'),
            get_help('award_number'),
            get_help('award_url')]
    return render_template('award.html',
                           title=title,
                           form=form,
                           help=help,
                           related_project=related_project)


def populate_award_form(form: AwardForm, award_node: Node):
    funder_name = ''
    award_title = ''
    funder_identifier = ''  # FIX ME - should be list
    award_number = ''
    award_url = ''

    if award_node:
        funder_name_node = award_node.find_child(names.FUNDERNAME)
        if funder_name_node and funder_name_node.content:
            funder_name = funder_name_node.content

        award_title_node = award_node.find_child(names.TITLE)
        if award_title_node and award_title_node.content:
            award_title = award_title_node.content

        funder_identifiers = []
        funder_identifier_nodes = award_node.find_all_children(names.FUNDERIDENTIFIER)
        for funder_identifier_node in funder_identifier_nodes:
            if funder_identifier_node.content:
                funder_identifiers.append(funder_identifier_node.content)
        funder_identifier = ','.join(funder_identifiers)

        award_number_node = award_node.find_child(names.AWARDNUMBER)
        if award_number_node and award_number_node.content:
            award_number = award_number_node.content

        award_url_node = award_node.find_child(names.AWARDURL)
        if award_url_node and award_url_node.content:
            award_url = award_url_node.content

    form.funder_name.data = funder_name
    form.award_title.data = award_title
    form.funder_identifier.data = funder_identifier
    form.award_number.data = award_number
    form.award_url.data = award_url


@proj_bp.route('/related_project_select/<filename>', methods=['GET', 'POST'])
def related_project_select(filename=None):
    form = RelatedProjectSelectForm(filename=filename)

    # Process POST
    if request.method == 'POST':
        form_value = request.form
        form_dict = form_value.to_dict(flat=False)
        url = related_project_select_post(filename, form, form_dict,
                                  'POST', PAGE_RELATED_PROJECT_SELECT, PAGE_METHOD_STEP_SELECT,
                                          PAGE_DONOR, PAGE_PROJECT)  #PT5/26
#PT5/26                                  PAGE_OTHER_ENTITY_SELECT, PAGE_PROJECT)
        return redirect(url)

    # Process GET
    return related_project_select_get(filename=filename, form=form)


def related_project_select_get(filename=None, form=None):
    # Process GET
    project_list = []
    title = 'Related Projects'
    eml_node = load_eml(filename=filename)

    if eml_node:
        project_list = list_related_projects(eml_node)

    set_current_page('project')
    help = [get_help('related_project')]
    return render_template('related_project_select.html', title=title,
                           filename=filename,
                           project_list=project_list,
                           form=form, help=help)


def related_project_select_post(filename=None, form=None, form_dict=None,
                        method=None, this_page=None, back_page=None,
                        next_page=None, edit_page=None):
    node_id = None
    new_page = None
    if form_dict:
        for key in form_dict:
            val = form_dict[key][0]  # value is the first list element
            if val == BTN_BACK:
                new_page = back_page
            elif val == BTN_NEXT or val == BTN_SAVE_AND_CONTINUE:
                new_page = next_page
            elif val == BTN_EDIT:
                new_page = edit_page
                node_id = key
            elif val == BTN_REMOVE:
                new_page = this_page
                node_id = key
                remove_related_project(filename, node_id)
            elif val == BTN_HIDDEN_CHECK:
                new_page = PAGE_CHECK
            elif val == BTN_HIDDEN_SAVE:
                new_page = this_page
            elif val == BTN_HIDDEN_DOWNLOAD:
                new_page = PAGE_DOWNLOAD
            elif val == BTN_HIDDEN_NEW:
                new_page = PAGE_CREATE
            elif val == BTN_HIDDEN_OPEN:
                new_page = PAGE_OPEN
            elif val == BTN_HIDDEN_CLOSE:
                new_page = PAGE_CLOSE
            elif val == UP_ARROW:
                new_page = this_page
                node_id = key
                process_up_button(filename, node_id)
            elif val == DOWN_ARROW:
                new_page = this_page
                node_id = key
                process_down_button(filename, node_id)
            elif val[0:3] == BTN_ADD:
                new_page = edit_page
                node_id = '1'
            elif val[0:4] == BTN_BACK:
                new_page = edit_page
                node_id = None

    if form.validate_on_submit():
        if new_page == edit_page:
            return url_for(new_page,
                           filename=filename,
                           node_id=node_id,
                           title='Related Project')
        else:
            return url_for(new_page,
                           filename=filename)


def list_related_projects(eml_node):
    related_projects = []
    project_node = eml_node.find_single_node_by_path([names.DATASET, names.PROJECT])
    if project_node:
        related_projects_nodes = project_node.find_all_children(names.RELATED_PROJECT)
        if related_projects_nodes:
            RP_Entry = collections.namedtuple(
                'RP_Entry', ["id", "label", "upval", "downval"],
                rename=False)
            for i, rp_node in enumerate(related_projects_nodes):
                title_node = rp_node.find_child(names.TITLE)
                if not title_node:
                    continue
                label = title_node.content
                id = rp_node.id
                upval = get_upval(i)
                downval = get_downval(i + 1, len(related_projects_nodes))
                rp_entry = RP_Entry(id=id, label=label, upval=upval, downval=downval)
                related_projects.append(rp_entry)
    return related_projects
