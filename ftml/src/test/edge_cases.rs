use std::rc::Rc;

use crate::{render::{html::HtmlRender, Render}, settings::{WikitextSettings, WikitextMode}, data::NullPageCallbacks, prelude::PageInfo};


#[test]
fn strikethrough() {
    let page_info = PageInfo::dummy();

    let settings = WikitextSettings::from_mode(WikitextMode::Page);
    let text = &mut String::from("-- a--");
    crate::preprocess(text);

    let tokens = crate::tokenize(&text);
    let result = crate::parse(&tokens, &page_info, Rc::new(NullPageCallbacks{}), &settings);
    let (tree, _warnings) = result.into();
    let html_output = HtmlRender.render(&tree, &page_info, Rc::new(NullPageCallbacks{}), &settings);

    assert_eq!(html_output.body, "<p>— a—</p>");
}

#[test]
fn paragraph_marker() {
    let page_info = PageInfo::dummy();

    let settings = WikitextSettings::from_mode(WikitextMode::Page);
    let text = &mut String::from(r#"[[div style="background: red"]]
= some centered text
= some centered text (not p) [[/div]]"#);
    crate::preprocess(text);

    let tokens = crate::tokenize(&text);
    let result = crate::parse(&tokens, &page_info, Rc::new(NullPageCallbacks{}), &settings);
    let (tree, _warnings) = result.into();
    let html_output = HtmlRender.render(&tree, &page_info, Rc::new(NullPageCallbacks{}), &settings);

    assert_eq!(html_output.body, "<div style=\"background: red\"><p style=\"text-align: center\">some centered text<br>some centered text (not p) </p></div>");
}

#[test]
fn glued_list() {
    let page_info = PageInfo::dummy();

    let settings = WikitextSettings::from_mode(WikitextMode::Page);
    let text = &mut String::from(r#"* item1
* item2

* item3
* item4"#);
    crate::preprocess(text);

    let tokens = crate::tokenize(&text);
    let result = crate::parse(&tokens, &page_info, Rc::new(NullPageCallbacks{}), &settings);
    let (tree, _warnings) = result.into();
    let html_output = HtmlRender.render(&tree, &page_info, Rc::new(NullPageCallbacks{}), &settings);

    assert_eq!(html_output.body, "<ul><li>item1</li><li>item2</li></ul><ul><li>item3</li><li>item4</li></ul>");
}