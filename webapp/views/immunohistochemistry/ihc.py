from flask import (
    Blueprint, flash, render_template, redirect, request, url_for
)

from webapp.views.immunohistochemistry.forms import (
    immunohistochemistryForm
)

from webapp.home.forms import (
    form_md5, is_dirty_form
)

from webapp.home.metapype_client import (
    load_eml, save_both_formats,
    add_child, create_immunohistochemistry, add_mother_metadata, new_child_node
)

from metapype.eml import names
from metapype.model.node import Node

from webapp.buttons import *
from webapp.pages import *

from webapp.home.views import select_post, non_breaking, set_current_page, get_help, get_helps

ihc_bp = Blueprint('ihc', __name__, template_folder='templates')


@ihc_bp.route('/immunohistochemistry/<filename>', methods=['GET', 'POST'])
def immunohistochemistry(filename=None):
    method = request.method
    node_id = '1'
    if filename:
        eml_node = load_eml(filename=filename)
        additional_metadata_node = eml_node.find_child(names.ADDITIONALMETADATA)
        if additional_metadata_node:
            mother_node = additional_metadata_node.find_child("mother")
            if mother_node:
                ihc_node = mother_node.find_child("immunohistochemistry")
                if ihc_node:
                    node_id = ihc_node.id
        else:
            add_mother_metadata(eml_node)
    # Added in 4/8/2022
    save_both_formats(filename, eml_node)
    set_current_page('ihc')
    help = [get_help('publisher')]
    return new_immunohistochemistry(filename=filename, node_id=node_id,
                                    method=method, node_name="immunohistochemistry",
                                    back_page=PAGE_CONTACT_SELECT, title='Immunohistochemistry',
                                    save_and_continue=True, help=help)


def new_immunohistochemistry(filename=None, node_id=None, method=None,
                             node_name=None, back_page=None, title=None,
                             next_page=None, save_and_continue=False, help=None,
                             project_node_id=None):
    if BTN_CANCEL in request.form:
        if not project_node_id:
            url = url_for(back_page, filename=filename)
        else:
            url = url_for(back_page, filename=filename, node_id=project_node_id)
        return redirect(url)

    form = immunohistochemistryForm(filename=filename)
    eml_node = load_eml(filename=filename)

    additional_metadata_node = eml_node.find_child(names.ADDITIONALMETADATA)
    mother_node = additional_metadata_node.find_child("mother")
    parent_node = mother_node

    # Could be important as well -NM 4/8/2022
    # new_page = select_new_page(back_page, next_page)
    # new_page = back_page

    # Could be important later -NM 4/8/2022
    # form_value = request.form
    # form_dict = form_value.to_dict(flat=False)
    # url = select_post(filename, form, form_dict,
    #                  'POST', PAGE_IHC, project_node_id=project_node_id)

    # Process POST
    save = False
    if is_dirty_form(form):
        save = True

    if form.validate_on_submit():
        if save:
            targetProtein = form.targetProtein.data
            primaryAntibody = Node("primaryAntibody", parent=None)
            clonality = form.clonality.data
            targetSpecies = form.targetSpecies.data
            hostSpecies = form.hostSpecies.data
            dilution = form.dilution.data
            lotNumber = form.lotNumber.data
            catNumber = form.catNumber.data
            source = form.source.data
            rrid = form.rrid.data
            secondaryAntibody = Node("secondaryAntibody", parent=None)
            targetSpecies_2 = form.targetSpecies_2.data
            hostSpecies_2 = form.hostSpecies_2.data
            dilution_2 = form.dilution_2.data
            lotNumber_2 = form.lotNumber_2.data
            catNumber_2 = form.catNumber_2.data
            source_2 = form.source_2.data
            rrid_2 = form.rrid_2.data
            detectionMethod = form.detectionMethod.data

            ihc_node = Node(node_name, parent=parent_node)

            new_ihc_node = create_immunohistochemistry(
                ihc_node,
                filename,
                targetProtein,
                primaryAntibody,
                clonality,
                targetSpecies,
                hostSpecies,
                dilution,
                lotNumber,
                catNumber,
                source,
                rrid,
                secondaryAntibody,
                targetSpecies_2,
                hostSpecies_2,
                dilution_2,
                lotNumber_2,
                catNumber_2,
                source_2,
                rrid_2,
                detectionMethod,
            )
            print("Test=", new_ihc_node)

            if node_id and len(node_id) != 1:
                old_ihc_node = Node.get_node_instance(node_id)
                if old_ihc_node:
                    old_ihc_parent_node = old_ihc_node.parent
                    old_ihc_parent_node.replace_child(old_ihc_node, new_ihc_node)
                else:
                    msg = f"No node found in the node store with node id {node_id}"
                    raise Exception(msg)
            else:
                parent_node.add_child(new_ihc_node)

            save_both_formats(filename=filename, eml_node=eml_node)

    # Process GET
    if node_id == '1':
        form.init_md5()
        # else:
        if parent_node:
            rp_nodes = parent_node.find_all_children(child_name=node_name)
            if rp_nodes:
                for ihc_node in rp_nodes:
                    if node_id == ihc_node.id:
                        populate_ihc_form(form, ihc_node)

    help = get_helps([node_name])
    return render_template('ihc.html', title=title, node_name=node_name,
                           form=form, next_page=next_page, save_and_continue=save_and_continue, help=help)


def populate_ihc_form(form: immunohistochemistryForm, node: Node):
    protein_node = node.find_child("targetProtein")
    if protein_node:
        proteinName_node = protein_node.find_child("proteinName")
        if proteinName_node:
            form.proteinName.data = proteinName_node.content

        geneSymbol_node = protein_node.find_all_children("geneSymbol")
        if geneSymbol_node:
            form.geneSymbol.data = geneSymbol_node.content

    user_id_nodes = node.find_all_children(names.USERID)
    for user_id_node in user_id_nodes:
        directory = user_id_node.attribute_value('directory')
        if directory == 'https://orcid.org':
            form.user_id.data = user_id_node.content
        else:
            form.org_id.data = user_id_node.content
            form.org_id_type.data = directory

    primaryAntibody_node = node.find_child("primaryAntibody")
    if primaryAntibody_node:
        clonality_node = primaryAntibody_node.find_child("clonality")
        if clonality_node:
            form.clonality.data = clonality_node.content

        targetSpecies_node_2 = primaryAntibody_node.find_child("targetSpecies")
        if targetSpecies_node_2:
            form.targetSpecies.data = targetSpecies_node_2.content

        hostSpecies_node_2 = primaryAntibody_node.find_child("hostSpecies")
        if hostSpecies_node_2:
            form.hostSpecies.data = hostSpecies_node_2.content

        dilution_node_2 = primaryAntibody_node.find_child("dilution")
        if dilution_node_2:
            form.dilution.data = dilution_node_2.content

        lotNumber_node_2 = primaryAntibody_node.find_child("lotNumber")
        if lotNumber_node_2:
            form.lotNumber.data = lotNumber_node_2.content

        catNumber_node_2 = primaryAntibody_node.find_child("catNumber")
        if catNumber_node_2:
            form.catNumber.data = catNumber_node_2.content

        source_node_2 = primaryAntibody_node.find_child("source")
        if source_node_2:
            form.source.data = source_node_2.content

        rrid_node_2 = primaryAntibody_node.find_child("RRID")
        if rrid_node_2:
            form.rrid.data = rrid_node_2.content

    secondaryAntibody_node = node.find_child("secondaryAntibody")
    if secondaryAntibody_node:
        targetSpecies_node_2 = secondaryAntibody_node.find_child("targetSpecies")
        if targetSpecies_node_2:
            form.targetSpecies_2.data = targetSpecies_node_2.content

        hostSpecies_node_2 = secondaryAntibody_node.find_child("hostSpecies")
        if hostSpecies_node_2:
            form.hostSpecies_2.data = hostSpecies_node_2.content

        dilution_node_2 = secondaryAntibody_node.find_child("dilution")
        if dilution_node_2:
            form.dilution_2.data = dilution_node_2.content

        lotNumber_node_2 = secondaryAntibody_node.find_child("lotNumber")
        if lotNumber_node_2:
            form.lotNumber_2.data = lotNumber_node_2.content

        catNumber_node_2 = secondaryAntibody_node.find_child("catNumber")
        if catNumber_node_2:
            form.catNumber_2.data = catNumber_node_2.content

        source_node_2 = secondaryAntibody_node.find_child("source")
        if source_node_2:
            form.source_2.data = source_node_2.content

        rrid_node_2 = secondaryAntibody_node.find_child("RRID")
        if rrid_node_2:
            form.rrid_2.data = rrid_node_2.content

    detectionMethod_node = node.find_child("detectionMethod")
    if detectionMethod_node:
        form.detectionMethod.data = detectionMethod_node.content

    form.md5.data = form_md5(form)


def select_new_page(back_page=None, next_page=None, edit_page=None):
    form_value = request.form
    form_dict = form_value.to_dict(flat=False)
    new_page = back_page
    if form_dict:
        for key in form_dict:
            val = form_dict[key][0]  # value is the first list element

            if val == BTN_BACK:
                new_page = back_page
                break
            elif val in (BTN_NEXT, BTN_SAVE_AND_CONTINUE):
                new_page = next_page
                break
            elif val == BTN_HIDDEN_NEW:
                new_page = PAGE_CREATE
                break
            elif val == BTN_HIDDEN_OPEN:
                new_page = PAGE_OPEN
                break
            elif val == BTN_HIDDEN_CLOSE:
                new_page = PAGE_CLOSE
                break

    return new_page
