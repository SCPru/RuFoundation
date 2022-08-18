use std::borrow::Cow;
use std::collections::HashMap;
use std::fmt::{Debug, Formatter, Result};

pub trait PageCallbacks: Debug {
    fn module_has_body(&self, module_name: Cow<str>) -> bool;
    fn render_module<'a>(&self, module_name: Cow<str>, params: HashMap<Cow<str>, Cow<str>>, body: Cow<str>) -> Cow<'static, str>;
    fn render_user<'a>(&self, user: Cow<str>, avatar: bool) -> Cow<'static, str>;
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
}

impl Debug for NullPageCallbacks {
    fn fmt(&self, f: &mut Formatter<'_>) -> Result {
        write!(f, "<NullPageCallbacks>")
    }
}