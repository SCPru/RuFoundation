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