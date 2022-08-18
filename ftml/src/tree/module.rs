/*
 * tree/module.rs
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

//! Representation of Wikidot modules, along with their context.

use std::borrow::Cow;
use std::collections::HashMap;
use crate::tree::clone::{string_map_to_owned, string_to_owned};

#[derive(Serialize, Deserialize, Debug, Clone, PartialEq, Eq)]
#[serde(rename_all = "kebab-case")]
pub struct Module<'t> {
    name: Cow<'t, str>,
    params: HashMap<Cow<'t, str>, Cow<'t, str>>,
    text: Cow<'t, str>,
}

impl<'t> Module<'t> {
    #[inline]
    pub fn new(
        name: Cow<'t, str>,
        params: HashMap<Cow<'t, str>, Cow<'t, str>>,
        text: Cow<'t, str>
    ) -> Self {
        Module {
            name,
            params,
            text
        }
    }

    #[inline]
    pub fn name(&self) -> &Cow<str> {
        &self.name
    }

    #[inline]
    pub fn params(&self) -> &HashMap<Cow<str>, Cow<str>> {
        &self.params
    }

    #[inline]
    pub fn text(&self) -> &Cow<str> {
        &self.text
    }

    pub fn to_owned(&self) -> Module<'static> {
        Module {
            name: string_to_owned(&self.name),
            params: string_map_to_owned(&self.params),
            text: string_to_owned(&self.text),
        }
    }
}
