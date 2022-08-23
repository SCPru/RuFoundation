use std::borrow::Cow;
use std::collections::HashMap;
use std::fmt::{Debug, Formatter, Result};
use wikidot_normalize::normalize;

use super::PageRef;
use super::page_info::PartialPageInfo;

#[derive(Debug)]
pub enum ExpressionResult<'t> {
    String(Cow<'t, str>),
    Bool(bool),
    Float(f64),
    Int(i64),
    None,
}

impl<'t> ToString for ExpressionResult<'t> {
    fn to_string(&self) -> String {
        match self {
            ExpressionResult::String(v) => v.to_string(),
            ExpressionResult::Bool(v) => v.to_string(),
            ExpressionResult::Float(v) => v.to_string(),
            ExpressionResult::Int(v) => v.to_string(),
            ExpressionResult::None => String::new()
        }
    }
}

pub trait PageCallbacks: Debug {
    fn module_has_body(&self, module_name: Cow<str>) -> bool;
    fn render_module<'a>(&self, module_name: Cow<str>, params: HashMap<Cow<str>, Cow<str>>, body: Cow<str>) -> Cow<'static, str>;
    fn render_user<'a>(&self, user: Cow<str>, avatar: bool) -> Cow<'static, str>;
    fn get_i18n_message<'a>(&self, message_id: Cow<str>) -> Cow<'static, str>;
    fn get_page_info<'a>(&self, page_refs: &Vec<PageRef<'a>>) -> Vec<PartialPageInfo<'static>>;
    fn evaluate_expression<'a>(&self, expression: Cow<str>) -> ExpressionResult<'static>;
    fn normalize<'a>(&self, name: Cow<str>) -> Cow<'static, str>;
}

pub struct NullPageCallbacks {}

impl PageCallbacks for NullPageCallbacks {
    fn module_has_body(&self, _module_name: Cow<str>) -> bool {
        return false
    }

    fn render_module<'a>(&self, module_name: Cow<str>, _params: HashMap<Cow<str>, Cow<str>>, _body: Cow<str>) -> Cow<'static, str> {
        return Cow::from(format!("NullModule[{module_name}]"));
    }

    fn render_user<'a>(&self, user: Cow<str>, _avatar: bool) -> Cow<'static, str> {
        return Cow::from(format!("NullUser[{user}]"));
    }

    fn get_i18n_message<'a>(&self, message_id: Cow<str>) -> Cow<'static, str> {
        let message_id = message_id.into_owned();

        let s = match message_id.as_str() {
            "button-copy-clipboard" => "Copy to Clipboard",
            "collapsible-open" => "+ open block",
            "collapsible-hide" => "- hide block",
            "table-of-contents" => "Table of Contents",
            "toc-open" => "Unfold",
            "toc-close" => "Fold",
            "footnote" => "Footnote",
            "footnote-block-title" => "Footnotes",
            "image-context-bad" => "No images in this context",
            _ => {
                error!("Unknown message requested (key {message_id})");
                "?"
            }
        };

        Cow::from(s)
    }

    fn get_page_info<'a>(&self, page_refs: &Vec<PageRef<'a>>) -> Vec<PartialPageInfo<'static>> {
        return page_refs.iter().map(|x| PartialPageInfo{page_ref: x.to_owned(), exists: false, title: None}).collect()
    }

    fn evaluate_expression<'a>(&self, _expression: Cow<str>) -> ExpressionResult<'static> {
        ExpressionResult::None
    }

    fn normalize<'a>(&self, name: Cow<str>) -> Cow<'static, str> {
        let mut result = name.to_string();
        normalize(&mut result);
        Cow::from(result)
    }
}

impl Debug for NullPageCallbacks {
    fn fmt(&self, f: &mut Formatter<'_>) -> Result {
        write!(f, "<NullPageCallbacks>")
    }
}