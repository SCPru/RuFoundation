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

use crate::data::PageInfo;
use crate::prelude::PageCallbacks;
use crate::settings::WikitextSettings;
use crate::tree::{ImageSource, LinkLabel, LinkLocation, Module};
use crate::url::BuildSiteUrl;
use std::borrow::Cow;
use std::rc::Rc;
use strum_macros::IntoStaticStr;
use wikidot_normalize::normalize;

#[derive(Debug)]
pub struct Handle {
    callbacks: Rc<dyn PageCallbacks>
}

impl Handle {
    pub fn new(callbacks: Rc<dyn PageCallbacks>) -> Self {
        Handle { callbacks }
    }

    pub fn render_module(
        &self,
        buffer: &mut String,
        module: &Module,
        mode: ModuleRenderMode,
    ) {
        info!(
            "Rendering module '{}' (mode '{}')",
            module.name(),
            mode.name(),
        );

        match mode {
            ModuleRenderMode::Html => {
                str_write!(buffer, "<p>TODO: module {}</p>", module.name());
            }
            ModuleRenderMode::Text => {
                str_write!(buffer, "TODO: module {}", module.name());
            }
        }
    }

    pub fn get_page_title(&self, _site: &str, _page: &str) -> Option<String> {
        info!("Fetching page title");

        // TODO
        Some(format!("TODO: actual title ({_site} {_page})"))
    }

    pub fn get_page_exists(&self, _site: &str, _page: &str) -> bool {
        info!("Checking page existence");

        // For testing
        #[cfg(test)]
        if _page == "missing" {
            return false;
        }

        // TODO
        true
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

    pub fn get_link_label<F>(
        &self,
        site: &str,
        link: &LinkLocation,
        label: &LinkLabel,
        f: F,
    ) where
        F: FnOnce(&str),
    {
        let page_title;
        let label_text = match *label {
            LinkLabel::Text(ref text) => text,
            LinkLabel::Url(Some(ref text)) => text,
            LinkLabel::Url(None) => match link {
                LinkLocation::Url(url) => url,
                LinkLocation::Page(page_ref) => page_ref.page(),
            },
            LinkLabel::Page => match link {
                LinkLocation::Url(url) => {
                    url.as_ref()
                }
                LinkLocation::Page(page_ref) => {
                    let (site, page) = page_ref.fields_or(site);
                    page_title = match self.get_page_title(site, page) {
                        Some(title) => title,
                        None => page_ref.to_string(),
                    };

                    &page_title
                }
            },
        };

        f(label_text);
    }

    pub fn get_message(&self, message: &str) -> String {
        self.callbacks.get_i18n_message(Cow::from(message)).as_ref().to_owned()
    }
}

impl BuildSiteUrl for Handle {
    fn build_url(&self, site: &str, path: &str) -> String {
        // TODO make this a parser setting
        // get url of wikijump instance here

        let path = {
            let mut path = str!(path);
            normalize(&mut path);
            path
        };

        // TODO
        format!("https://{site}.wikijump.com/{path}")
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
