/*
 * render/handle.rs
 *
 * ftml - Library to parse Wikidot text
 * Copyright (C) 2019-2022 Wikijump Team
 *
 * This program is free software: you can redistribute it and/or modify
 * it under the terms of the GNU Affero General Public License as published by
 * the Free Software Foundation, either version 3 of the License, or
 * (at your option) any later version.
 *
 * This program is distributed in the hope that it will be useful,
 * but WITHOUT ANY WARRANTY; without even the implied warranty of
 * MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
 * GNU Affero General Public License for more details.
 *
 * You should have received a copy of the GNU Affero General Public License
 * along with this program. If not, see <http://www.gnu.org/licenses/>.
 */

use crate::data::{PageInfo, PageRef, PartialPageInfo};
use crate::prelude::PageCallbacks;
use crate::settings::WikitextSettings;
use crate::tree::{ImageSource, LinkLabel, LinkLocation};
use std::borrow::Cow;
use std::collections::HashMap;
use std::rc::Rc;
use strum_macros::IntoStaticStr;

#[derive(Debug)]
pub struct Handle<'t> {
    callbacks: Rc<dyn PageCallbacks>,
    internal_links: HashMap<PageRef<'t>, PartialPageInfo<'t>>,
}

impl<'t> Handle<'t> {
    pub fn new(callbacks: Rc<dyn PageCallbacks>, raw_internal_links: &Vec<PartialPageInfo<'t>>) -> Self {
        let mut internal_links = HashMap::new();
        for info in raw_internal_links {
            internal_links.insert(info.page_ref.to_owned(), info.to_owned());
        }

        Handle { callbacks, internal_links }
    }

    pub fn get_page_title(&self, page_ref: &PageRef) -> Option<String> {
        info!("Fetching page title");

        match self.internal_links.get(page_ref) {
            Some(info) => {
                match &info.title {
                    Some(Cow::Borrowed("")) => None,
                    None => None,
                    Some(title) => Some(title.to_string())
                }
            },
            None => None
        }
    }

    pub fn get_page_exists(&self, page_ref: &PageRef) -> bool {
        info!("Checking page existence");

        match self.internal_links.get(page_ref) {
            Some(info) => info.exists,
            None => false
        }
    }

    pub fn get_image_link<'a>(
        &self,
        source: &ImageSource<'a>,
        info: &PageInfo,
        settings: &WikitextSettings,
    ) -> Option<Cow<'a, str>> {
        info!("Getting file link for image");

        let (site, page, file): (&str, Cow<str>, &str) = match source {
            ImageSource::Url(url) => return Some(Cow::clone(url)),
            ImageSource::File1 { .. }
            | ImageSource::File2 { .. }
                if !settings.allow_local_paths =>
            {
                warn!("Specified path image source when local paths are disabled");
                return None;
            }
            ImageSource::File1 { file } => (&info.site, info.full_name(), file),
            ImageSource::File2 { page, file } => (&info.site, page.to_owned(), file),
        };

        // cross-site images are unsupported
        if info.site != site {
            None
        } else {
            Some(Cow::Owned(format!("//{}/local--files/{page}/{file}", &info.media_domain)))
        }
    }

    pub fn get_iframe_link<'a>(
        &self,
        hash: &str,
        id: &str,
        info: &PageInfo,
    ) -> Cow<'a, str> {
        info!("Getting file link for iframe");
        Cow::Owned(format!("//{}/local--html/{}/{hash}-{id}", &info.media_domain, &info.full_name()))
    }

    pub fn get_link_label<F>(
        &self,
        link: &LinkLocation,
        label: &LinkLabel,
        f: F,
    ) where
        F: FnOnce(&str),
    {
        let page_title;
        let label_text = match *label {
            LinkLabel::Text(ref text) => Cow::from(text.as_ref()),
            LinkLabel::Url(Some(ref text)) => Cow::from(text.as_ref()),
            LinkLabel::Url(None) => match link {
                LinkLocation::Url(url) => Cow::from(url.as_ref()),
                LinkLocation::Page(page_ref, _) => Cow::from(page_ref.to_string().to_owned()),
            },
            LinkLabel::Page => match link {
                LinkLocation::Url(url) => {
                    Cow::from(url.as_ref())
                }
                LinkLocation::Page(page_ref, _) => {
                    page_title = match self.get_page_title(page_ref) {
                        Some(title) if !title.trim().is_empty() => title,
                        _ => page_ref.to_string(),
                    };

                    Cow::from(&page_title)
                }
            },
        };

        f(label_text.as_ref());
    }

    pub fn get_message(&self, message: &str) -> String {
        self.callbacks.get_i18n_message(Cow::from(message)).as_ref().to_owned()
    }

    pub fn get_html_injected_code(&self, html_id: &str) -> String {
        self.callbacks.get_html_injected_code(Cow::from(html_id)).as_ref().to_owned()
    }
}

#[derive(
    IntoStaticStr, Serialize, Deserialize, Debug, Hash, Copy, Clone, PartialEq, Eq,
)]
#[serde(rename_all = "kebab-case")]
pub enum ModuleRenderMode {
    Html,
    Text,
}

impl ModuleRenderMode {
    #[inline]
    pub fn name(self) -> &'static str {
        self.into()
    }
}
