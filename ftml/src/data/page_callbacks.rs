use std::borrow::Cow;
use std::collections::HashMap;
use std::fmt::Debug;

pub trait PageCallbacks: Debug {
    fn module_has_body(&self, _module_name: Cow<str>) -> bool {
        return false
    }

    fn render_module<'a>(&self, _module_name: Cow<str>, _params: HashMap<Cow<str>, Cow<str>>, _body: Cow<str>) -> Cow<'static, str> {
        return Cow::from("");
    }
}
