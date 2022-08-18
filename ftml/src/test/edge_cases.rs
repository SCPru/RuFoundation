use std::rc::Rc;

use crate::{render::{html::HtmlRender, Render}, settings::{WikitextSettings, WikitextMode}, data::NullPageCallbacks, prelude::PageInfo};

fn assert_rendered(input: &str, output: &str) {
    let page_info = PageInfo::dummy();

    let settings = WikitextSettings::from_mode(WikitextMode::Page);
    let text = &mut String::from(input);
    crate::preprocess(text);

    let tokens = crate::tokenize(&text);
    let result = crate::parse(&tokens, &page_info, Rc::new(NullPageCallbacks{}), &settings);
    let (tree, _warnings) = result.into();
    let html_output = HtmlRender.render(&tree, &page_info, Rc::new(NullPageCallbacks{}), &settings);

    assert_eq!(html_output.body, output);
}

#[test]
fn strikethrough() {
    assert_rendered("-- a--", "<p>— a—</p>");
}

#[test]
fn paragraph_marker() {
    assert_rendered(r#"[[div style="background: red"]]
= some centered text
= some centered text (not p) [[/div]]"#, "<div style=\"background: red\"><p style=\"text-align: center\">some centered text<br>some centered text (not p) </p></div>");
}

#[test]
fn glued_list() {
    assert_rendered(r#"* item1
* item2

* item3
* item4"#, "<ul><li>item1</li><li>item2</li></ul><ul><li>item3</li><li>item4</li></ul>");
}

#[test]
fn eighteen_plus() {
    assert_rendered("**18+**", "<p><strong>18+</strong></p>");
}