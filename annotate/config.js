var NEW_POST_MARKER = "++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++";
var END_POST_MARKER = "---------------------------------------------------------------------------------------------------------";
var FRONTMATTER_MARKER = "---";
var ANNOTATION_PLACEHOLDER = "[Annotation content goes here]"

function setLogo_() {
    // Get DocumentProperties
    var props = PropertiesService.getDocumentProperties();
    // Ask for data
    var ui = DocumentApp.getUi();
    var result = ui.prompt(
        'Sidebar logo',
        'Enter the sidebar logo url:',
        ui.ButtonSet.OK);
    var button = result.getSelectedButton();
    var url = result.getResponseText();
    if (button == ui.Button.OK) {
        props.setProperty('sidebar_logo', url);
    }
}


