use std::borrow::Cow;
use std::collections::HashMap;
use std::fmt::Debug;

pub trait PageCallbacks<'a>: Debug {
    fn module_has_body(&self, _module_name: Cow<'a, str>) -> bool {
        return false
    }

    fn render_module(&self, _module_name: Cow<'a, str>, _params: HashMap<Cow<'a, str>, Cow<'a, str>>, _body: Cow<'a, str>) -> Cow<'a, str> {
        return Cow::from("");
    }
}
